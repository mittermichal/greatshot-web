from flask import request, redirect, url_for, render_template, send_from_directory, jsonify, flash, current_app
import os
import subprocess
import app.Libtech3
import urllib.request
from urllib.error import HTTPError
import urllib.parse
import app.gamestv
from app.utils import get_gtv_demo, check_disk_space, LowDiskSpaceException
import app.ftp
import re
from app.forms import ExportFileForm, ExportMatchLinkForm, CutForm, RenderForm
# from markdown import markdown
from app.models import Render
from sqlalchemy import desc
from app.export import parse_output
from sqlalchemy.orm.exc import NoResultFound
from time import strftime, gmtime
from glob import iglob
from app.views.renders import render_new
import random
import string
from flask import Blueprint

flask_app = Blueprint('main', __name__)


def upload(request):
    check_disk_space()
    if 'file' in request.files:
        file = request.files['file']
        filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) + file.filename
        file.save(os.path.join('app', 'upload', filename))
    elif request.form['filename'] != '':
        filename = request.form['filename']
    elif request.form['filepath'] != '':
        filename = request.form['filepath']
    else:
        raise Exception("No filename selected for cut")
    return filename


@flask_app.route('/download/')
@flask_app.route('/download/<path:path>')
def download_static(path=''):
    full_path = os.path.normpath(os.path.join('app', 'download', path))
    if os.path.isfile(full_path):
        as_attachment = request.args.get('dl', '0') == '1'
        # http://stackoverflow.com/questions/24612366/flask-deleting-uploads-after-they-have-been-downloaded
        return send_from_directory(directory='download', filename=path, as_attachment=as_attachment)
    elif os.path.isdir(full_path):
        lst = sorted(
            [{
                'name': f,
                'path': os.path.join(path, f).replace("\\", "/"),
                'ctime': os.path.getctime(os.path.join(full_path, f)),
                'formatted_ctime': strftime('%c', gmtime(os.path.getctime(os.path.join(full_path, f)))),
                'isdir': os.path.isdir(os.path.join(full_path, f))
            } for f in os.listdir(full_path)],
            key=lambda f: [f['isdir'], f['ctime']],
            reverse=True
        )
        return render_template('download_list.html', files=lst)
    else:
        flash("file not found")
        return download_static(''), 404


# TODO exclude POV playerstate/entity
@flask_app.route('/cut', methods=['GET', 'POST'])
def cut():
    form1, form2 = ExportFileForm(request.form), ExportMatchLinkForm(request.form)
    cut_form = CutForm(request.form)
    if request.form.__contains__('start'):
        try:
            if request.form['gtv_match_id'] != '' and request.form['map_number'] != '':
                filename = get_gtv_demo(
                    re.findall(r'(\d+)', request.form['gtv_match_id'])[0],
                    int(request.form['map_number'])-1
                )
            else:
                filename = upload(request)
            app.Libtech3.cut(
                current_app.config['PARSERPATH'],
                ('app/upload/' + filename, request.form['filepath'])[request.form['filepath'] != ''],
                'app/download/cuts/demo-out.dm_84',
                request.form['start'], request.form['end'], request.form['cut_type'], request.form['client_num'])
        except Exception as e:
            flash(e)
            return render_template('cut.html', cut_form=cut_form, form1=form1, form2=form2)
        return send_from_directory(directory='download/cuts', filename='demo-out.dm_84', as_attachment=True,
                                   attachment_filename='demo-out.dm_84')
    else:
        return render_template('cut.html', cut_form=cut_form, form1=form1, form2=form2)


# TODO export only POV events for dm_84 demo
@flask_app.route('/export', methods=['GET', 'POST'])
def export():
    form1, form2 = ExportFileForm(request.form), ExportMatchLinkForm(request.form)
    if request.method == 'POST':
        cut_form = CutForm(request.form)
        rndr_form = RenderForm(request.form)
        if request.form['gtv_match_id'] != '' and request.form['map_number'] != '':
            return redirect(url_for('main.export_get',
                                    gtv_match_id=re.findall(r'(\d+)', request.form['gtv_match_id'])[0],
                                    map_num=str(request.form['map_number']))
                                )

        filename = upload(request)
        return redirect(url_for('main.export_demo_file', filename=filename))
    try:
        ettv_demos_path = current_app.config['ETTV_DEMOS_PATH']
        ettv_demos = [
            url_for('main.export_ettv', path=urllib.parse.quote(os.path.relpath(x, ettv_demos_path), safe=''))
            for x in sorted(
                [f for f in iglob(ettv_demos_path + '**/*.tv_84', recursive=True)],
                key=lambda f: os.path.getmtime(f),
                reverse=True
            )
        ]
        return render_template('export.html', form1=form1, form2=form2, ettv_demos=ettv_demos)
    except IndexError:
        print('indexerror')
        pass

    return render_template('export.html', form1=form1, form2=form2)


@flask_app.route('/export/ettv_demo/<path>')
def export_ettv(path):
    ettv_demos_path = current_app.config['ETTV_DEMOS_PATH']
    path = os.path.join(os.path.normcase(ettv_demos_path), os.path.normcase(urllib.parse.unquote(path)))
    print(path)
    cut_form = CutForm()
    rndr_form = RenderForm()
    filename = os.path.abspath(path)
    print(filename)
    cut_form.filepath.data = filename
    # cut_form.filename = 'aaa'
    indexer = 'indexTarget/%s/exportJsonFile/%s.txt/exportBulletEvents/1/exportDemo/1/exportChatMessages/1/exportRevives/1'
    if os.name == 'posix':
        indexer = indexer.replace('/', '\\')
    arg = indexer % (filename, filename)
    if not os.path.isfile(path + '.txt') or request.args.get('live', False):
        subprocess.call([current_app.config['PARSERPATH'], 'indexer', arg])
    parsed_output = parse_output(
        open(path + '.txt', 'r', encoding='utf-8', errors='ignore').readlines(),
        cut_form.gtv_match_id.data)
    return render_template('export-out.html', cut_form=cut_form, rndr_form=rndr_form,
                           out=open(path + '.txt', 'r').read(),
                           parser_out=parsed_output)


@flask_app.route('/export/gtv/<export_id>')
def export_get_match(export_id):
    renders = Render.query.order_by(desc(Render.id)).filter(Render.gtv_match_id == export_id)
    return render_template('renders.html', renders=renders, export_id=export_id)


@flask_app.route('/export/<gtv_match_id>/<map_num>')
@flask_app.route('/export/gtv/<gtv_match_id>/<map_num>')
def export_get(gtv_match_id, map_num, render=False, html=True):
    gtv_match_id = int(gtv_match_id)
    map_num = max(int(map_num)-1, 0)
    if html:
        cut_form = CutForm()
        rndr_form = RenderForm()
        cut_form.gtv_match_id.data = gtv_match_id
        cut_form.map_number.data = map_num + 1
    renders = Render.query.order_by(desc(Render.id)).filter(Render.gtv_match_id == gtv_match_id,
                                                            Render.map_number == map_num)

    form1, form2 = ExportFileForm(), ExportMatchLinkForm()

    filename = str(gtv_match_id) + '_' + str(map_num) + '.tv_84'
    export_out_file_path = 'app/download/exports/' + filename + '.txt'
    if not os.path.isfile(export_out_file_path):
        try:
            filename = get_gtv_demo(gtv_match_id, map_num)
        except Exception as e:
            flash(str(e))
            return render_template('export.html', form1=form1, form2=form2)
        else:
            arg = current_app.config['INDEXER'] % (filename, filename)
            subprocess.call([current_app.config['PARSERPATH'], 'indexer', arg])
    f = open(export_out_file_path, 'r', encoding='utf-8', errors='ignore')
    out = f.readlines()
    f.close()

    parser_out = parse_output(out, gtv_match_id, map_num)
    if render:
        for player in parser_out['players']:
            for spree in player['sprees']:
                render_new(filename, spree[0]['dwTime'] - 2000,
                           2000 + spree[len(spree) - 1]['dwTime'], 1,
                           player['bClientNum'],
                           player['szCleanName'] + 's ' + str(len(spree)) + '-man kill', gtv_match_id, map_num, None)
    if html:
        return render_template('export-out.html', renders=renders,
                               cut_form=cut_form, rndr_form=rndr_form,
                               out="".join(out),
                               parser_out=parser_out,
                               map_num=map_num,
                               export_id=gtv_match_id
                               )
    else:
        return parser_out


@flask_app.route('/export/<filename>')
def export_demo_file(filename):
    if not os.path.isfile('app/upload/' + filename):
        flash("Demo not found.")
        return redirect(url_for('main.export'))
    export_out_file_path = 'app/download/exports/' + filename + '.txt'
    if not os.path.isfile(export_out_file_path):
        arg = current_app.config['INDEXER'] % (filename, filename)
        subprocess.call([current_app.config['PARSERPATH'], 'indexer', arg])
    parsed_output = parse_output(open(export_out_file_path, 'r',
                                      encoding='utf-8', errors='ignore').readlines())
    cut_form = CutForm()
    rndr_form = RenderForm()
    cut_form.filename.data = filename
    # TODO: retrieve clips that are from this demo
    return render_template('export-out.html', filename=filename, cut_form=cut_form, rndr_form=rndr_form,
                           out=open('app/download/exports/' + filename + '.txt',
                                    'r', encoding='utf-8', errors='ignore').read(),
                           parser_out=parsed_output)


@flask_app.route('/')
def index():
    return render_template('layout.html', msg='<a href="https://github.com/mittermichal/greatshot-web">github</a>')


@flask_app.route('/get_maps', methods=['POST'])
def get_maps():
    gtv_link = request.form['gtv_link']
    try:
        demo_id = app.gamestv.getMatchDemosId(re.findall(r'(\d+)', gtv_link)[0])
    except IndexError:
        return jsonify({'count': -3})
    except HTTPError:
        return jsonify({'count': -1})
    try:
        return jsonify({'count': len(app.gamestv.getDemosLinks(demo_id))})
    except HTTPError:
        return jsonify({'count': -2})


@flask_app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))


@flask_app.app_errorhandler(NoResultFound)
def handle_no_result_exception(_):
    flash('Item not found')
    return render_template('layout.html'), 404


@flask_app.app_errorhandler(404)
def page_not_found(e):
    flash(e)
    return render_template('layout.html'), 404


@flask_app.app_errorhandler(LowDiskSpaceException)
def handle_low_disk_space_exception(e):
    flash(e)
    return render_template('layout.html'), 500
