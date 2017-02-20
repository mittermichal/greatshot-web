#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, jsonify, flash
import os
import subprocess
import app.Libtech3
import urllib.request
from urllib.request import urlopen, HTTPError, URLError
import ftplib
import app.gamestv
import app.ftp
import re
from app.forms import ExportFileForm, ExportMatchLinkForm, CutForm, RenderForm
import markdown
import eventexport
import tasks
from app.db import db_session
from app.models import Render
from sqlalchemy import desc
from app.export import parse_output

flask_app = Flask(__name__)
flask_app.config.from_pyfile('config.cfg')


def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
           request.accept_mimetypes[best] > \
           request.accept_mimetypes['text/html']


@flask_app.route('/renders/<render_id>')
def render_get(render_id):
    render = Render.query.filter(Render.id == render_id).first()
    if render.streamable_short != None:
        return redirect('http://streamable.com/' + render.streamable_short)
    result = tasks.render.AsyncResult(render.celery_id)
    if request_wants_json():
        data = result.result or result.state
        # print(data)
        return jsonify(data)
    if result.successful():
        render.streamable_short = result.get()
        db_session.commit()
    return render_template('render.html', render=render)


def render_new(filename, start, end, cut_type, client_num, title, gtv_match_id, map_number, player):
    if gtv_match_id == '':
        filename_orig = filename
    else:
        filename_orig = 'upload/' + str(gtv_match_id) + '_' + str(map_number) + '.tv_84'
    filename_cut = 'download/' + str(gtv_match_id) + '_' + str(map_number) + '_' + str(client_num) + '_' + str(
        start) + '_' + str(end) + '.dm_84'
    if gtv_match_id != '' and not os.path.exists(filename_orig):
        demo_url = app.gamestv.getDemosLinks(app.gamestv.getMatchDemosId(gtv_match_id))[int(map_number)]
        urllib.request.urlretrieve(demo_url, filename_orig)
    app.Libtech3.cut(flask_app.config['PARSERPATH'], filename_orig, filename_cut, int(start) - 2000, end, cut_type,
                     client_num)
    result = tasks.render.delay(flask_app.config['APPHOST'] + '/' + filename_cut, start,end, title, player['name'] if (player!=None) else None, player['country'] if (player!=None) else None,etl=False)
    r = Render(result.id, title, gtv_match_id, map_number, client_num, player['id'] if (player!=None) else None )
    db_session.add(r)
    db_session.flush()
    db_session.commit()
    return r.id


@flask_app.route('/renders', methods=['GET', 'POST'])
def renders_list():
    if request.method == 'GET':
        renders = Render.query.order_by(desc(Render.id)).all()
        for render in renders:
            if render.streamable_short == None:
                result = tasks.render.AsyncResult(render.celery_id)
                if result.successful():
                    render.streamable_short = result.get()
        db_session.commit()
        return render_template('renders.html', renders=renders)
    if request.method == 'POST':
        form = RenderForm(request.form)
        render_id = render_new('upload/' + request.form['filename'], str(int(request.form['start'])),
                               request.form['end'],
                               request.form['cut_type'], request.form['client_num'], form.data['title'],
                               form.data['gtv_match_id'], form.data['map_number'], None)
        return redirect(url_for('render_get', render_id=render_id))


def spree_time_interval(spree):
    return {'start': spree[0]['dwTime'], 'end': spree[len(spree) - 1]['dwTime']}


@flask_app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in set(['tv_84', 'dm_84'])


# http://flask.pocoo.org/docs/0.11/patterns/fileuploads/
def upload(request):
    if 'uselast' in request.form:
        print('uselast')
    elif request.form['matchId'] != '':
        if request.form['map'] == '':
            raise Exception("map number")
        else:
            # return 'demo.tv_84'
            match_id = re.findall('(\d+)', request.form['matchId'])[0]
            demo_ids = app.gamestv.getMatchDemosId(int(match_id))
            try:
                demo_links = app.gamestv.getDemosLinks(demo_ids)[int(request.form['map']) - 1]
            except IndexError:
                raise Exception("demo not found")
            filename = str(match_id) + '_' + str(int(request.form['map']) - 1) + '.tv_84'
            urllib.request.urlretrieve(demo_links, 'upload/' + filename)
            return filename
    else:
        if 'file' not in request.files:
            return 'demo.tv_84'
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return 'demo.tv_84'
        if not file or not allowed_file(file.filename):
            return 'demo.tv_84'
        filename = 'demo.' + file.filename.rsplit('.', 1)[1]
        file.save(os.path.join('upload', filename))
        return filename
    return 'demo.tv_84'


@flask_app.route('/download/<path:filename>')
def download_static(filename):
    # http://stackoverflow.com/questions/24612366/flask-deleting-uploads-after-they-have-been-downloaded
    return send_from_directory(directory='download', filename=filename)


# TODO exclude POV playerstate/entity
@flask_app.route('/cut', methods=['GET', 'POST'])
def cut():
    form1, form2 = ExportFileForm(), ExportMatchLinkForm()
    cut_form = CutForm()
    if request.form.__contains__('start'):
        filename = upload(request)
        app.Libtech3.cut(
            flask_app.config['PARSERPATH'], 'upload/' + filename, 'download/demo-out.dm_84', request.form['start'],
            request.form['end'], request.form['cut_type'], request.form['client_num'])
        return send_from_directory(directory='download', filename='demo-out.dm_84', as_attachment=True,
                                   attachment_filename='demo-out.dm_84')
    else:
        return render_template('cut.html', cut_form=cut_form, form1=form1, form2=form2)


# TODO export only POV events for dm_84 demo
@flask_app.route('/export', methods=['GET', 'POST'])
def export():
    form1, form2 = ExportFileForm(), ExportMatchLinkForm()
    if request.method == 'POST':
        cut_form = CutForm()
        rndr_form = RenderForm()
        if request.form['matchId'] != '' and request.form['map'] != '':
            try:
                response = export_get(re.findall('(\d+)', request.form['matchId'])[0],
                                      str(int(request.form['map']) - 1))
            except Exception as e:
                print('404', e)
            else:
                return response
        try:
            filename = upload(request)
        except HTTPError:
            flash("Probably no demos available for this match")
            return render_template('export.html', form1=form1, form2=form2)
        except Exception as e:
            flash(e)
            return render_template('export.html', form1=form1, form2=form2)
        else:
            arg = flask_app.config['INDEXER'] % (filename)
            subprocess.call([flask_app.config['PARSERPATH'], 'indexer', arg])
            if request.form['matchId'] != '' and request.form['map'] != '':
                rndr_form.gtv_match_id.data = re.findall('(\d+)', request.form['matchId'])[0]
                rndr_form.map_number.data = int(request.form['map'])-1

                try:
                    export_save(re.findall('(\d+)', request.form['matchId'])[0], str(int(request.form['map']) - 1))
                except TimeoutError:
                    print("ftp timeout")
            else:
                rndr_form.filename.data = filename
            parsed_output = parse_output(open('download/out.json', 'r').readlines())
            # make gtv comment
            # retrieve clips that are from this demo
            return render_template('export-out.html', filename=filename, cut_form=cut_form, rndr_form=rndr_form,
                                   out=open('download/out.json', 'r').read(),
                                   parser_out=parsed_output)
    return render_template('export.html', form1=form1, form2=form2)


@flask_app.route('/export/last')
def export_last():
    cut_form = CutForm()
    rndr_form = RenderForm()
    return render_template('export-out.html', cut_form=cut_form, rndr_form=rndr_form,
                           out=open('download/out.json', 'r').read(),
                           parser_out=parse_output(open('download/out.json', 'r').readlines()))


def generate_ftp_path(export_id):
    path = ''
    for c in export_id:
        path = path + c + '/'
    return path


@flask_app.route('/export/<export_id>')
def export_get_match(export_id):
    renders = Render.query.order_by(desc(Render.id)).filter(Render.gtv_match_id == export_id)
    return render_template('renders.html', renders=renders, export_id=export_id)


@flask_app.route('/export/<export_id>/<map_num>')
def export_get(export_id, map_num, render=False, html=True):
    if html:
        cut_form = CutForm()
        rndr_form = RenderForm()
        rndr_form.gtv_match_id.data = export_id
        rndr_form.map_number.data = map_num
    renders = Render.query.order_by(desc(Render.id)).filter(Render.gtv_match_id == export_id,
                                                            Render.map_number == map_num)
    ftp_url = 'ftp://' + flask_app.config['FTP_USER'] + ':' + flask_app.config['FTP_PW'] + '@' + flask_app.config[
        'FTP_HOST'] + '/exports/' + generate_ftp_path(export_id) + map_num + '.json'
    try:
        out = list(map(lambda x: x.decode('utf-8', 'replace'), urlopen(ftp_url).readlines()))
    except (HTTPError, URLError) as e:
        raise e
        return "not found"

    parser_out = parse_output(out)
    if render:
        for player in parser_out['players']:
            for spree in player['sprees']:
                render_new(spree[0]['dwTime'] - 2000, 2000 + spree[len(spree) - 1]['dwTime'], 1, player['bClientNum'],
                           player['szCleanName'] + 's ' + str(len(spree)) + '-man kill', export_id, map_num, None)
    if html:
        return render_template('export-out.html', renders=renders, cut_form=cut_form, rndr_form=rndr_form,
                               out="".join(out),
                               parser_out=parser_out)
    else:
        return parser_out


def export_save(export_id, map):
    path = 'exports/' + generate_ftp_path(export_id)
    session = ftplib.FTP(flask_app.config['FTP_HOST'], flask_app.config['FTP_USER'], flask_app.config['FTP_PW'])
    app.ftp.chdir(session, path[:-1])
    file = open('download/out.json', 'rb')
    session.storbinary('STOR ' + str(map) + '.json', file)
    file.close()
    session.quit()


@flask_app.route('/')
def index():
    return render_template('layout.html', msg=markdown.markdown(open('README.md', 'r').read()))


@flask_app.route('/matches', methods=['GET', 'POST'])
def matches():
    return render_template('layout.html', msg='soon™')


@flask_app.route('/players', methods=['GET', 'POST'])
def players():
    return render_template('layout.html', msg='soon™')


@flask_app.route('/getMaps', methods=['POST'])
def getMaps():
    gtv_link = request.form['gtv_link']
    try:
        demoId = app.gamestv.getMatchDemosId(re.findall('(\d+)', gtv_link)[0])
    except IndexError:
        return jsonify({'count': -3})
    except (HTTPError):
        return jsonify({'count': -1})
    try:
        return jsonify({'count': len(app.gamestv.getDemosLinks(demoId))})
    except (HTTPError):
        return jsonify({'count': -2})


# TODO: upload raw video from worker
'''
@flask_app.route('/raw')
def raw():
  return send_from_directory(directory='.', filename='render.mp4', as_attachment=True, attachment_filename='render.mp4')
'''
if __name__ == "__main__":
    flask_app.run(port=5111, host='0.0.0.0')
