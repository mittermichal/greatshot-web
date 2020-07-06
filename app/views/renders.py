from flask import Blueprint, render_template, request, url_for, jsonify, redirect, current_app
from werkzeug.utils import secure_filename

from app.models import Render
from app.db import db_session
from sqlalchemy import desc
from app.forms import RenderForm, CutForm
from app.utils import check_auth, authenticate, get_gtv_demo, flash_errors
import app.Libtech3
import tasks
from datetime import timedelta
import os
import requests
from .. import socketio

renders = Blueprint('renders', __name__)


@renders.route('/renders/<render_id>', methods=['GET'])
def render_get(render_id):
    render = Render.query.filter(Render.id == render_id).one()
    video_path = 'download/renders/' + str(render_id) + '.mp4'
    video_url = url_for('static', filename=video_path)
    video_exists = os.path.isfile('app/' + video_path)
    return render_template(
        'render.html', render=render,
        video_url=video_url, video_exists=video_exists,
        download_url=url_for('main.download_static', path='renders/' + str(render.id) + '.mp4', dl=1)
    )


@socketio.on('get_render_status')
def on_render_status(render_id):
    render = Render.query.filter(Render.id == render_id).one()
    socketio.emit('status-'+str(render_id), {
        'status_msg': render.status_msg,
        'progress': render.progress
    })


@renders.route('/renders/<render_id>/status', methods=['GET'])
def render_status_get(render_id):
    render = Render.query.filter(Render.id == render_id).one()
    data = {'status_msg': render.status_msg,
            'progress': render.progress}
    return jsonify(data)


@renders.route('/renders/<render_id>', methods=['POST'])
def render_post(render_id):
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    db_session.query(Render).filter(Render.id == render_id).update(
        {Render.status_msg: request.json['status_msg'], Render.progress: request.json['progress']}
    )
    db_session.commit()
    socketio.emit('status-'+str(render_id), request.json)
    if request.json['status_msg'] == 'finished' and 'RENDER_FINISHED_WEBHOOK' in current_app.config.keys():
        try:
            requests.post(
                current_app.config['RENDER_FINISHED_WEBHOOK'],
                json={
                    'content': current_app.config['APPHOST']+url_for(
                        'static', filename='download/renders/' + render_id + '.mp4'
                    )
                }
            )
        except requests.RequestException:
            pass
    return "", 200


@renders.route('/get_worker_last_beat')
def r_get_worker_last_beat():
    diff = int(tasks.redis_broker.client.time()[0] - tasks.get_worker_last_beat())
    return jsonify('last online: {} ago'.format(str(timedelta(seconds=diff))))


@renders.route('/status')
def status():
    diff = int(tasks.redis_broker.client.time()[0] - tasks.get_worker_last_beat())
    msg = "Render worker is "
    if diff <= 60:
        msg += 'online.'
    else:
        msg += 'offline. last online: {} ago'.format(str(timedelta(seconds=diff)))
    return render_template('layout.html', msg=msg)


def render_new(filename, start, end, cut_type, client_num, title, gtv_match_id, map_number, name=None, country=None, crf=23):
    if gtv_match_id == '':
        filename_orig = filename
    else:
        filename_orig = 'app/upload/' + get_gtv_demo(gtv_match_id, map_number)
    filename_cut = 'download/cuts/' + str(gtv_match_id) + '_' + str(map_number) + '_' + str(client_num) + '_' + str(
        start) + '_' + str(end) + '.dm_84'

    app.Libtech3.cut(
        current_app.config['PARSERPATH'],
        filename_orig,
        os.path.join('app', filename_cut),
        int(start) - 2000, end, cut_type,
        client_num
    )
    r = Render(
        title=title,
        status_msg='started', progress=1,
        gtv_match_id=gtv_match_id,
        map_number=map_number,
        client_num=client_num,
        start=start, end=end
    )
    db_session.add(r)
    db_session.commit()
    tasks.render.send(
        r.id,
        current_app.config['APPHOST'] + url_for('static', filename=filename_cut),
        start, end,
        name, country,
        etl=False, crf=crf
    )
    return r.id


@renders.route('/renders', methods=['GET', 'POST'])
def renders_list():
    if request.method == 'POST':
        form = RenderForm(request.form)
        cut_form = CutForm(request.form)
        # TODO: dynamic validation of: - client number
        #                              - start and end time
        if form.validate_on_submit() and cut_form.validate_on_submit():
            map_number = int(cut_form.data['map_number']) - 1 if cut_form.data['map_number'] != '' else None
            filepath = ('upload/' + cut_form.data['filename'], request.form['filepath'])[request.form['filepath'] != '']
            render_id = render_new(filepath, str(int(cut_form.data['start'])), cut_form.data['end'],
                                   cut_form.data['cut_type'], cut_form.data['client_num'], form.data['title'],
                                   cut_form.data['gtv_match_id'], map_number,
                                   form.data['name'], form.data['country'], form.data['crf'])
            return redirect(url_for('renders.render_get', render_id=render_id))
        else:
            flash_errors(form)
            flash_errors(cut_form)
            renders = Render.query.order_by(desc(Render.id)).all()
            return render_template('renders.html', renders=renders)
    else:
        renders = Render.query.order_by(desc(Render.id)).all()
        return render_template('renders.html', renders=renders)


@renders.route('/renders', methods=['PUT'])
def render_upload():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    try:
        for filename, file in request.files.items():
            name = secure_filename(request.files[filename].name)
            file.save(os.path.join('app', 'download', 'renders', name))
            return name
        return jsonify({'error': 'no file'})
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)})
