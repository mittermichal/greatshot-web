#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, redirect, url_for, render_template, send_from_directory, jsonify, flash
import os
import subprocess
import app.Libtech3
import urllib.request
from urllib.error import HTTPError
import app.gamestv
import app.ftp
import re
from app.forms import ExportFileForm, ExportMatchLinkForm, CutForm, RenderForm
import markdown
import tasks
from app.status_worker import get_worker_last_beat, redis_broker
from app.db import db_session
from app.models import Render
from sqlalchemy import desc
from app.export import parse_output
from sqlalchemy.orm.exc import NoResultFound
from time import time
from datetime import timedelta

flask_app = Flask(__name__)
flask_app.config.from_pyfile('config.cfg')


def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


@flask_app.route('/renders/<render_id>')
def render_get(render_id):
    render = Render.query.filter(Render.id == render_id).one()
    if request_wants_json():
        data = {'status_msg': render.status_msg,
                'progress': render.progress}
        return jsonify(data)
    return render_template('render.html', render=render)


@flask_app.route('/get_worker_last_beat')
def r_get_worker_last_beat():
    diff = int(redis_broker.client.time()[0] - get_worker_last_beat())
    return jsonify('last online: {} ago'.format(str(timedelta(seconds=diff))))


@flask_app.route('/status')
def status():
    diff = int(redis_broker.client.time()[0] - get_worker_last_beat())
    msg = "Render worker is "
    if diff <= 60:
        msg += 'online.'
    else:
        msg += 'offline. last online: {} ago'.format(str(timedelta(seconds=diff)))
    return render_template('layout.html', msg=msg)


def render_new(filename, start, end, cut_type, client_num, title, gtv_match_id, map_number, player):
    if gtv_match_id == '':
        filename_orig = filename
    else:
        filename_orig = 'upload/' + get_gtv_demo(gtv_match_id, map_number)
    filename_cut = 'download/cuts/' + str(gtv_match_id) + '_' + str(map_number) + '_' + str(client_num) + '_' + str(
        start) + '_' + str(end) + '.dm_84'

    app.Libtech3.cut(flask_app.config['PARSERPATH'], filename_orig, filename_cut, int(start) - 2000, end, cut_type,
                     client_num)
    r = Render(
        title=title,
        status_msg='started', progress=1,
        gtv_match_id=gtv_match_id,
        map_number=map_number,
        client_num=client_num,
        start=start, end=end
    )
    db_session.add(r)
    db_session.flush()
    db_session.commit()
    tasks.render.send(
        r.id,
        flask_app.config['APPHOST'] + '/' + filename_cut,
        start, end, title,
        player.name if (player is not None) else None,
        player.country if (player is not None) else None,
        etl=False
    )
    return r.id


@flask_app.route('/renders', methods=['GET', 'POST'])
def renders_list():
    if request.method == 'GET':
        renders = Render.query.order_by(desc(Render.id)).all()
        return render_template('renders.html', renders=renders)
    if request.method == 'POST':
        form = RenderForm(request.form)
        cut_form = CutForm(request.form)

        # TODO: player nickname and country to pass to new render
        db_player = None

        # try:
        map_number = int(cut_form.data['map_number']) - 1 if cut_form.data['map_number'] != '' else None
        render_id = render_new('upload/' + cut_form.data['filename'], str(int(cut_form.data['start'])),
                               cut_form.data['end'],
                               cut_form.data['cut_type'], cut_form.data['client_num'], form.data['title'],
                               cut_form.data['gtv_match_id'], map_number, db_player)
        # except Exception as e:
        #     flash(str(e))
        #     return redirect(url_for('export'))
        #     return redirect(url_for('export',_anchor='render-form'), code=307)
        return redirect(url_for('render_get', render_id=render_id))


def spree_time_interval(spree):
    return {'start': spree[0]['dwTime'], 'end': spree[len(spree) - 1]['dwTime']}


@flask_app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in {'tv_84', 'dm_84'}


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
            filename = request.form['filename']
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
    return send_from_directory(directory='download', filename=filename)


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
                flask_app.config['PARSERPATH'], 'upload/' + filename, 'download/cuts/demo-out.dm_84', request.form['start'],
                request.form['end'], request.form['cut_type'], request.form['client_num'])
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
            try:
                return redirect(url_for('export_get',
                                        export_id=re.findall(r'(\d+)', request.form['gtv_match_id'])[0],
                                        map_num=str(request.form['map_number']))
                                )
            #except HTTPError:
            #    flash("Probably no demos available for this match")
            except Exception as e:
                flash(e)
                return render_template('export.html', form1=form1, form2=form2)

        filename = upload(request)
        arg = flask_app.config['INDEXER'] % (filename, filename)
        subprocess.call([flask_app.config['PARSERPATH'], 'indexer', arg])
        if request.form['gtv_match_id'] != '' and request.form['map_number'] != '':
            cut_form.gtv_match_id.data = re.findall(r'(\d+)', request.form['map_number'])[0]
            cut_form.map_number.data = int(request.form['map_number'])-1
        else:
            cut_form.filename.data = filename
        parsed_output = parse_output(open('download/exports/'+filename+'.json', 'r',
                                          encoding='utf-8', errors='ignore').readlines(),
                                     cut_form.gtv_match_id.data)
        # make gtv comment
        # retrieve clips that are from this demo
        return render_template('export-out.html', filename=filename, cut_form=cut_form, rndr_form=rndr_form,
                               out=open('download/exports/'+filename+'.json', 'r', encoding='utf-8', errors='ignore').read(),
                               parser_out=parsed_output)
    return render_template('export.html', form1=form1, form2=form2)


@flask_app.route('/export/last')
def export_last():
    cut_form = CutForm()
    render_form = RenderForm()
    return render_template('export-out.html', cut_form=cut_form, rndr_form=render_form,
                           out=open('download/exports/out.json', 'r').read(),
                           parser_out=parse_output(open('download/exports/out.json', 'r').readlines()))


def generate_ftp_path(export_id):
    path = ''
    for c in str(export_id):
        path = path + c + '/'
    return path


@flask_app.route('/export/<export_id>')
def export_get_match(export_id):
    renders = Render.query.order_by(desc(Render.id)).filter(Render.gtv_match_id == export_id)
    return render_template('renders.html', renders=renders, export_id=export_id)


def get_gtv_demo(gtv_match_id, map_num):
    filename = str(gtv_match_id) + '_' + str(map_num) + '.tv_84'
    if not os.path.exists('upload/'+filename):
        try:
            demo_id = app.gamestv.getMatchDemosId(int(gtv_match_id))
        except HTTPError:
            error_message = "Match not found"
            raise Exception(error_message)
        except IndexError:
            try:
                demo_links = app.gamestv.getDemosDownloadLinks(gtv_match_id)[int(map_num)]
            except IndexError:
                error_message = "Match not available for replay"
                raise Exception(error_message)
        else:
            try:
                demo_links = app.gamestv.getDemosLinks(demo_id)[int(map_num)]
            except IndexError:
                error_message = "demo not found"
                raise Exception(error_message)
            except HTTPError:
                error_message = "no demos for this match"
                raise Exception(error_message)
            except TypeError:
                error_message = "demos are probably private but possible to download"
                raise Exception(error_message)
        try:
            urllib.request.urlretrieve(demo_links, 'upload/' + filename)
        except urllib.error.HTTPError:
            raise Exception("Download from gamestv.org failed - 404")
    return filename


@flask_app.route('/export/<export_id>/<map_num>')
def export_get(export_id, map_num, render=False, html=True):
    export_id = int(export_id)
    map_num = int(map_num)-1
    if html:
        cut_form = CutForm()
        rndr_form = RenderForm()
        cut_form.gtv_match_id.data = export_id
        cut_form.map_number.data = map_num + 1
    renders = Render.query.order_by(desc(Render.id)).filter(Render.gtv_match_id == export_id,
                                                            Render.map_number == map_num)

    form1, form2 = ExportFileForm(), ExportMatchLinkForm()
    error_response = render_template('export.html', form1=form1, form2=form2)
    try:
        filename = get_gtv_demo(export_id, map_num)
    except Exception as e:
        flash(str(e))
        return error_response
    else:
        arg = flask_app.config['INDEXER'] % (filename, filename)
        subprocess.call([flask_app.config['PARSERPATH'], 'indexer', arg])
        f = open('download/exports/'+filename+'.json', 'r', encoding='utf-8', errors='ignore')
        out = f.readlines()
        f.close()
        # os.remove('download/exports/'+filename+'.json')
        # return filename

    parser_out = parse_output(out, export_id)
    if render:
        for player in parser_out['players']:
            for spree in player['sprees']:
                render_new(filename, spree[0]['dwTime'] - 2000,
                           2000 + spree[len(spree) - 1]['dwTime'], 1,
                           player['bClientNum'],
                           player['szCleanName'] + 's ' + str(len(spree)) + '-man kill', export_id, map_num, None)
    if html:
        return render_template('export-out.html', renders=renders,
                               cut_form=cut_form, rndr_form=rndr_form,
                               out="".join(out),
                               parser_out=parser_out,
                               map_num=map_num,
                               export_id=export_id
                               )
    else:
        return parser_out


@flask_app.route('/')
def index():
    return render_template('layout.html', msg=markdown.markdown(open('README.md', 'r').read()))


@flask_app.route('/matches', methods=['GET', 'POST'])
def matches():
    return render_template('layout.html', msg='soon™')


# TODO player db
"""
@flask_app.route('/players', methods=['GET', 'POST'])
def players():
    if request.method == 'POST':
        player_form = PlayerForm(request.form)

        #r = Render(result.id, title, gtv_match_id, map_number, client_num, player.id if (player != None) else None)
        player = Player()
        match_player = MatchPlayer()
        player_form.populate_obj(player)
        db_session.add(player)
        db_session.flush()


        player_form.populate_obj(match_player)
        match_player.player_id=player.id
        db_session.add(match_player)
        db_session.flush()
        db_session.commit()
        return str(match_player.id)
    else:
        players=Player.query.all()
        return render_template('players.html', players=players)

@flask_app.route('/players/<player_id>', methods=['GET', 'POST'])
def player_get(player_id):
    player=Player.query.filter(Player.id == player_id).first()
    renders=Render.query.filter(Render.player_id == player_id)
    return render_template('player.html', player=player, renders=renders)
"""


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


@flask_app.errorhandler(NoResultFound)
def handle_no_result_exception(error):
    flash('Item not found')
    return render_template('layout.html'), 404


@flask_app.errorhandler(404)
def page_not_found(e):
    flash(e)
    return render_template('layout.html'), 404


if __name__ == "__main__":
    flask_app.run(port=5111, host='0.0.0.0')
