from flask import request, redirect, url_for, render_template, send_from_directory, jsonify, flash, current_app
import os
import subprocess
import app.Libtech3
from app.utils import check_disk_space, LowDiskSpaceException
import re
from app.forms import ExportFileForm, CutForm
from app.export import parse_output
from sqlalchemy.orm.exc import NoResultFound
from time import strftime, gmtime
from glob import iglob
import random
import string
from flask import Blueprint

flask_app = Blueprint('main', __name__)


def upload():
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
        return send_from_directory(directory='download', path=path, as_attachment=as_attachment)
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
    export_file_form = ExportFileForm(request.form)
    cut_form = CutForm(request.form)
    if request.form.__contains__('start'):
        try:
            filename = upload()
            app.Libtech3.cut(
                current_app.config['PARSERPATH'],
                ('app/upload/' + filename, request.form['filepath'])[request.form['filepath'] != ''],
                'app/download/cuts/demo-out.dm_84',
                request.form['start'], request.form['end'], request.form['cut_type'], request.form['client_num'])
        except Exception as e:
            flash(str(e))
            return render_template('cut.html', cut_form=cut_form, form1=export_file_form)
        return send_from_directory(directory='download/cuts', path='demo-out.dm_84', as_attachment=True,
                                   download_name='demo-out.dm_84')
    else:
        return render_template('cut.html', cut_form=cut_form, form1=export_file_form)


# TODO export only POV events for dm_84 demo
@flask_app.route('/export', methods=['GET', 'POST'])
def export():
    export_file_form = ExportFileForm(request.form)
    if request.method == 'POST':
        filename = upload()
        return redirect(url_for('main.export_demo_file', filename=filename))
    return render_template('export.html', form1=export_file_form)


@flask_app.route('/export/<filename>')
def export_demo_file(filename):
    if not os.path.isfile('app/upload/' + filename):
        flash("Demo not found.")
        return redirect(url_for('main.export'))
    export_out_file_path = 'app/download/exports/' + filename + '.txt'
    if not os.path.isfile(export_out_file_path):
        arg = current_app.config['INDEXER'] % (filename, filename)
        # print(subprocess.check_output(['pwd']).decode())
        # print(subprocess.check_output(['ls', '-lah']).decode())
        res = subprocess.run([current_app.config['PARSERPATH'], 'indexer', arg], capture_output=True)
        print(res.stdout.decode())
        if 'DemoIdent -> Cannot open demo' in res.stdout.decode():
            raise Exception(f"parser can't open demo file, indexer argument: {arg}")

    spree_timeout, hs_spree_timeout = parse_timeouts()
    parsed_output = parse_output(
        open(export_out_file_path, 'r', encoding='utf-8', errors='ignore').readlines(),
        spree_timeout, hs_spree_timeout
    )
    cut_form = CutForm()
    cut_form.filename.data = filename
    # TODO: retrieve clips that are from this demo
    return render_template(
        'export-out.html', filename=filename, cut_form=cut_form,
        raw_out_path=export_out_file_path.replace('app/download/', ''),
        spree_timeout=spree_timeout,
        hs_spree_timeout=hs_spree_timeout,
        parser_out=parsed_output
    )


@flask_app.route('/')
def index():
    return redirect(url_for('main.export'))


def parse_timeouts():
    spree = int(request.args.get('spree-timeout', 6000))
    hs_spree = int(request.args.get('hs-spree-timeout', 5000))
    if spree <= 0 or hs_spree <= 0:
        spree = 6000
        hs_spree = 5000
        flash("Timeout has to be positive integer")
    return spree, hs_spree


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
