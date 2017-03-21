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
from app.models import Render,Player,MatchPlayer
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
        return render_template('render.html', render=render)
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
    result = tasks.render.delay(flask_app.config['APPHOST'] + '/' + filename_cut, start,end, title, player.name if (player!=None) else None, player.country if (player!=None) else None,etl=False)
    r = Render(result.id, title, gtv_match_id, map_number, client_num, player.id if (player!=None) else None )
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
        cut_form = CutForm(request.form)
        mp = None
        if cut_form.data['gtv_match_id']!='' and cut_form.data['client_num']!='':
            mp = MatchPlayer.query.filter(MatchPlayer.gtv_match_id == int(cut_form.data['gtv_match_id']),MatchPlayer.client_num == int(cut_form.data['client_num'])).first()
        if mp != None:
            db_player = Player.query.filter(Player.id == mp.player_id).first()
        else:
            db_player=None
        try:
            render_id = render_new('upload/' + cut_form.data['filename'], str(int(cut_form.data['start'])),
                               cut_form.data['end'],
                               cut_form.data['cut_type'], cut_form.data['client_num'], form.data['title'],
                               cut_form.data['gtv_match_id'], cut_form.data['map_number'],db_player)
        except Exception as e:
            flash(str(e))
            #return redirect(url_for('export'))
            return redirect(url_for('export',_anchor='render-form'), code=307)
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
    else:
        if 'file' in request.files:
            file = request.files['file']
            filename = 'demo.' + file.filename.rsplit('.', 1)[1]
            file.save(os.path.join('upload', filename))
        elif request.form['filename'] != '':
            filename=request.form['filename']
        else:
            raise Exception("No filename selected for cut")
        # if user does not select file, browser also
        # submit a empty part without filename
        #if file.filename == '':
        #    return 'demo.tv_84'
        #if not file or not allowed_file(file.filename):
        #    return 'demo.tv_84'

        return filename
    return 'demo.tv_84'


@flask_app.route('/download/<path:filename>')
def download_static(filename):
    # http://stackoverflow.com/questions/24612366/flask-deleting-uploads-after-they-have-been-downloaded
    return send_from_directory(directory='download', filename=filename)


# TODO exclude POV playerstate/entity
@flask_app.route('/cut', methods=['GET', 'POST'])
def cut():
    form1, form2 = ExportFileForm(request.form), ExportMatchLinkForm(request.form)
    cut_form = CutForm(request.form)
    if request.form.__contains__('start'):
        if request.form['gtv_match_id'] != '' and request.form['map_number'] != '':
            filename = get_gtv_demo(re.findall('(\d+)', request.form['gtv_match_id'])[0],request.form['map_number'])
        else:
            filename = upload(request)
        try:
            app.Libtech3.cut(
                flask_app.config['PARSERPATH'], 'upload/' + filename, 'download/demo-out.dm_84', request.form['start'],
                request.form['end'], request.form['cut_type'], request.form['client_num'])
        except Exception as e:
            flash(e)
            return render_template('cut.html', cut_form=cut_form, form1=form1, form2=form2)
        return send_from_directory(directory='download', filename='demo-out.dm_84', as_attachment=True,
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
            try:
                return redirect(url_for('export_get',export_id=re.findall('(\d+)', request.form['gtv_match_id'])[0],map_num=str((request.form['map_number']))))
                response = export_get(re.findall('(\d+)', request.form['gtv_match_id'])[0],
                                      str(int(request.form['map_number'])))
            #except HTTPError:
            #    flash("Probably no demos available for this match")
            except Exception as e:
                flash(e)
                return render_template('export.html', form1=form1, form2=form2)
            else:
                return response
        filename = upload(request)
        arg = flask_app.config['INDEXER'] % (filename,filename)
        subprocess.call([flask_app.config['PARSERPATH'], 'indexer', arg])
        if request.form['gtv_match_id'] != '' and request.form['map_number'] != '':
            cut_form.gtv_match_id.data = re.findall('(\d+)', request.form['map_number'])[0]
            cut_form.map_number.data = int(request.form['map_number'])-1
        else:
            cut_form.filename.data = filename
        parsed_output = parse_output(open('download/'+filename+'.json', 'r').readlines(),cut_form.gtv_match_id.data)
        # make gtv comment
        # retrieve clips that are from this demo
        return render_template('export-out.html', filename=filename, cut_form=cut_form, rndr_form=rndr_form,
                               out=open('download/'+filename+'.json', 'r').read(),
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
    for c in str(export_id):
        path = path + c + '/'
    return path


@flask_app.route('/export/<export_id>')
def export_get_match(export_id):
    renders = Render.query.order_by(desc(Render.id)).filter(Render.gtv_match_id == export_id)
    return render_template('renders.html', renders=renders, export_id=export_id)

def get_gtv_demo(gtv_match_id,map_num):
    filename = str(gtv_match_id) + '_' + str(map_num) + '.tv_84'
    if not os.path.exists('upload/'+filename):
        demo_ids = app.gamestv.getMatchDemosId(int(gtv_match_id))
        demo_links = app.gamestv.getDemosLinks(demo_ids)[int(map_num)]
        urllib.request.urlretrieve(demo_links, 'upload/' + filename)
    return filename

@flask_app.route('/export/<export_id>/<map_num>')
def export_get(export_id, map_num, render=False, html=True):
    export_id=int(export_id)
    map_num=int(map_num)-1
    if html:
        cut_form = CutForm()
        rndr_form = RenderForm()
        cut_form.gtv_match_id.data = export_id
        cut_form.map_number.data = map_num
    renders = Render.query.order_by(desc(Render.id)).filter(Render.gtv_match_id == export_id,
                                                            Render.map_number == map_num)
    ftp_url = 'ftp://' + flask_app.config['FTP_USER'] + ':' + flask_app.config['FTP_PW'] + '@' + flask_app.config[
        'FTP_HOST'] + '/exports/' + generate_ftp_path(str(export_id)) + str(map_num) + '.json'
    try:
        #raise Exception
        out = list(map(lambda x: x.decode('utf-8', 'replace'), urlopen(ftp_url).readlines()))
    except (Exception,HTTPError, URLError):
        # return 'demo.tv_84'
        form1, form2 = ExportFileForm(), ExportMatchLinkForm()
        error_response=render_template('export.html', form1=form1, form2=form2)
        match_id = export_id
        try:
            demo_ids = app.gamestv.getMatchDemosId(int(match_id))
        except HTTPError:
            flash("Match not found")
            return error_response
        except IndexError:
            flash("Match not available for replay")
            return error_response
        try:
            demo_links = app.gamestv.getDemosLinks(demo_ids)[map_num]
        except IndexError:
            flash("demo not found")
            return error_response
        except HTTPError:
            flash("no demos for this match")
            return error_response
        except (TypeError):
            flash("demos are probably private but possible to download")
            return error_response
        else:
            filename = str(match_id) + '_' + str(map_num)
            urllib.request.urlretrieve(demo_links, 'upload/' + filename + '.tv_84')
            arg = flask_app.config['INDEXER'] % (filename+ '.tv_84',filename)
            subprocess.call([flask_app.config['PARSERPATH'], 'indexer', arg])
            try:
                export_save(export_id, map_num)
            except Exception as e:
                print(str(e))
            f=open('download/'+filename+'.json', 'r')
            out=f.readlines()
            f.close()
            os.remove('download/'+filename+'.json')
            #return filename

    parser_out = parse_output(out,export_id)
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
    file = open('download/'+str(export_id) + '_' + str(map)+'.json', 'rb')
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
    players=Player.query.all()
    return render_template('players.html', players=players)

@flask_app.route('/players/<player_id>', methods=['GET', 'POST'])
def player_get(player_id):
    player=Player.query.filter(Player.id == player_id).first()
    renders=Render.query.filter(Render.player_id == player_id)
    return render_template('player.html', player=player, renders=renders)


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
