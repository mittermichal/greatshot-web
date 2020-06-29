from flask import Flask, request, redirect, url_for, render_template, send_from_directory, jsonify, flash, Response
import os
import subprocess
import app.Libtech3
import urllib.request
from urllib.error import HTTPError
import urllib.parse
import requests
import app.gamestv
import app.ftp
import re
from app.forms import ExportFileForm, ExportMatchLinkForm, CutForm, RenderForm
from markdown import markdown
import tasks
from app.db import db_session
from app.models import Render
from sqlalchemy import desc
from app.export import parse_output
from sqlalchemy.orm.exc import NoResultFound
from time import strftime, gmtime
from datetime import timedelta
from glob import glob, iglob
from werkzeug.utils import secure_filename
import tasks_config
from flask_paginate import Pagination, get_page_parameter
from flask_login import LoginManager
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Roles, UserRoles
from app.forms import LoginForm, RegistrationForm, UserForm
from app.exceptions import NotAuthorizedException


flask_app = Flask(__name__)
flask_app.config.from_pyfile('config.cfg')
login = LoginManager(flask_app)


def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


@flask_app.route('/renders/<render_id>', methods=['GET'])
def render_get(render_id):
    render = Render.query.filter(Render.id == render_id).one()
    video_path = 'download/renders/' + str(render_id) + '.mp4'
    video_url = url_for('static', filename=video_path)
    video_exists = os.path.isfile(video_path)
    return render_template(
        'render.html', render=render,
        video_url=video_url, video_exists=video_exists,
        download_url=url_for('download_static', path='renders/' + str(render.id) + '.mp4', dl=1)
    )


@flask_app.route('/renders/<render_id>/status', methods=['GET'])
def render_status_get(render_id):
    render = Render.query.filter(Render.id == render_id).one()
    data = {'status_msg': render.status_msg,
            'progress': render.progress}
    return jsonify(data)


@flask_app.route('/renders/<render_id>', methods=['POST'])
def render_post(render_id):
    db_session.query(Render).filter(Render.id == render_id).update(
        {Render.status_msg: request.json['status_msg'], Render.progress: request.json['progress']}
    )
    db_session.commit()
    if request.json['status_msg'] == 'finished' and 'RENDER_FINISHED_WEBHOOK' in flask_app.config.keys():
        try:
            requests.post(
                flask_app.config['RENDER_FINISHED_WEBHOOK'],
                json={
                    'content': flask_app.config['APPHOST']+url_for(
                        'static', filename='download/renders/' + render_id + '.mp4'
                    )
                }
            )
        except requests.RequestException:
            pass
    return "", 200


@flask_app.route('/get_worker_last_beat')
def r_get_worker_last_beat():
    diff = int(tasks.redis_broker.client.time()[0] - tasks.get_worker_last_beat())
    return jsonify('last online: {} ago'.format(str(timedelta(seconds=diff))))


@flask_app.route('/status')
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
    db_session.commit()
    tasks.render.send(
        r.id,
        flask_app.config['APPHOST'] + '/' + filename_cut,
        start, end,
        name, country,
        etl=False, crf=crf
    )
    return r.id


@flask_app.route('/renders', methods=['GET', 'POST'])
def renders_list():
    if request.method == 'GET':
        page = request.args.get(get_page_parameter(), type=int, default=1)
        per_page = 20
        query = Render.query.order_by(desc(Render.id))
        renders = query.limit(per_page).offset(per_page*(page-1)).all()
        pagination = Pagination(
            page=page,
            per_page=per_page,
            total=query.count(),
            record_name='renders',
            bs_version=4
        )
        return render_template('renders.html', renders=renders, pagination=pagination)
    if request.method == 'POST':
        form = RenderForm(request.form)
        cut_form = CutForm(request.form)
        # TODO: dynamic validation of: - client number
        #                              - start and end time
        if form.validate_on_submit() and cut_form.validate_on_submit() and cut_form.validate_render_length():
            map_number = int(cut_form.data['map_number']) - 1 if cut_form.data['map_number'] != '' else None
            filepath = ('upload/' + cut_form.data['filename'], request.form['filepath'])[request.form['filepath'] != '']
            render_id = render_new(filepath, str(int(cut_form.data['start'])), cut_form.data['end'],
                                   cut_form.data['cut_type'], cut_form.data['client_num'], form.data['title'],
                                   cut_form.data['gtv_match_id'], map_number,
                                   form.data['name'], form.data['country'], form.data['crf'])
            return redirect(url_for('render_get', render_id=render_id))
        else:
            flash_errors(form)
            flash_errors(cut_form)
            renders = Render.query.order_by(desc(Render.id)).all()
            return render_template('renders.html', renders=renders)


def spree_time_interval(spree):
    return {'start': spree[0]['dwTime'], 'end': spree[len(spree) - 1]['dwTime']}


@flask_app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in {'tv_84', 'dm_84'}


# http://flask.pocoo.org/docs/0.11/patterns/fileuploads/
# @flask_app.route('/uploads/<path:filename>')

def upload(request):
    if 'file' in request.files:
        file = request.files['file']
        filename = 'demo.' + file.filename.rsplit('.', 1)[1]
        file.save(os.path.join('upload', filename))
    elif request.form['filename'] != '':
        filename = request.form['filename']
    elif request.form['filepath'] != '':
        filename = request.form['filepath']
    else:
        raise Exception("No filename selected for cut")
    # if user does not select file, browser also
    # submit a empty part without filename
    #if file.filename == '':
    #    return 'demo.tv_84'
    #if not file or not allowed_file(file.filename):
    #    return 'demo.tv_84'

    return filename


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == tasks_config.STREAMABLE_NAME and password == tasks_config.STREAMABLE_PW


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


@flask_app.route('/renders', methods=['PUT'])
def render_upload():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    try:
        for filename, file in request.files.items():
            name = secure_filename(request.files[filename].name)
            file.save(os.path.join('download/renders', name))
            return name
        return jsonify({'error': 'no file'})
    except Exception as e:
        print(e)
        return jsonify({'error': e})


@flask_app.route('/download/')
@flask_app.route('/download/<path:path>')
def download_static(path=''):
    full_path = os.path.normpath(os.path.join('download', path))
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
                flask_app.config['PARSERPATH'],
                ('upload/' + filename, request.form['filepath'])[request.form['filepath'] != ''],
                'download/cuts/demo-out.dm_84',
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
        export_out_file_path = 'download/exports/'+filename+'.txt'
        if not os.path.isfile(export_out_file_path):
            arg = flask_app.config['INDEXER'] % (filename, filename)
            subprocess.call([flask_app.config['PARSERPATH'], 'indexer', arg])
        if request.form['gtv_match_id'] != '' and request.form['map_number'] != '':
            cut_form.gtv_match_id.data = re.findall(r'(\d+)', request.form['map_number'])[0]
            cut_form.map_number.data = int(request.form['map_number'])-1
        else:
            cut_form.filename.data = filename
        parsed_output = parse_output(open(export_out_file_path, 'r',
                                          encoding='utf-8', errors='ignore').readlines(),
                                     cut_form.gtv_match_id.data)
        # make gtv comment
        # retrieve clips that are from this demo
        return render_template('export-out.html', filename=filename, cut_form=cut_form, rndr_form=rndr_form,
                               out=open('download/exports/'+filename+'.txt',
                                        'r', encoding='utf-8', errors='ignore').read(),
                               parser_out=parsed_output)
    try:
        ettv_demos_path = flask_app.config['ETTV_DEMOS_PATH']
        ettv_demos = [
            url_for('export_ettv', path=urllib.parse.quote(os.path.relpath(x, ettv_demos_path), safe=''))
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
    ettv_demos_path = flask_app.config['ETTV_DEMOS_PATH']
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
    if not os.path.isfile(path + '.txt'):
        subprocess.call([flask_app.config['PARSERPATH'], 'indexer', arg])
    parsed_output = parse_output(
        open(path + '.txt', 'r', encoding='utf-8', errors='ignore').readlines(),
        cut_form.gtv_match_id.data)
    return render_template('export-out.html', cut_form=cut_form, rndr_form=rndr_form,
                           out=open(path + '.txt', 'r').read(),
                           parser_out=parsed_output)


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
        export_out_file_path = 'download/exports/'+filename+'.txt'
        if not os.path.isfile(export_out_file_path):
            arg = flask_app.config['INDEXER'] % (filename, filename)
            subprocess.call([flask_app.config['PARSERPATH'], 'indexer', arg])
        f = open(export_out_file_path, 'r', encoding='utf-8', errors='ignore')
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
    return render_template('layout.html', msg=markdown(open('README.md', 'r').read()))


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


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


@flask_app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(nick=form.nick.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid nick or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@flask_app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@flask_app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(nick=form.nick.data)
        user.set_password(form.password.data)
        db_session.add(user)
        db_session.commit()
        flash('User registered')
        return redirect(url_for('login'))
    else:
        flash_errors(form)
    return render_template('register.html', title='Register', form=form)


@flask_app.route('/users', methods=['GET'])
@login_required
def users():
    if Roles.ADMIN.value not in [user_role.role for user_role in current_user.roles]:
        raise NotAuthorizedException
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 20
    query = User.query
    users = query.limit(per_page).offset(per_page*(page-1)).all()
    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=query.count(),
        record_name='users',
        bs_version=4
    )
    return render_template('users.html', users=users, pagination=pagination)


@flask_app.route('/user/<user_id>', methods=['GET', 'POST'])
@login_required
def user_r(user_id):
    if Roles.ADMIN.value not in [user_role.role for user_role in current_user.roles]:
        raise NotAuthorizedException
    user = User.query.filter(User.id == user_id).one()
    form = UserForm(roles=[user_role.role for user_role in user.roles])
    if form.validate_on_submit():
        UserRoles.query.filter(UserRoles.user_id == user_id).delete()
        db_session.commit()
        user.roles = [UserRoles(user_id=user_id, role=int(role)) for role in form.roles.data]
        db_session.commit()
        flash('User edited')
        return redirect(url_for('user_r', user_id=user_id))
    else:
        flash_errors(form)
    return render_template('user.html', user=user, form=form)


@flask_app.route('/user/<user_id>/delete', methods=['POST'])
@login_required
def user_delete(user_id):
    if Roles.ADMIN.value not in [user_role.role for user_role in current_user.roles]:
        raise NotAuthorizedException
    User.query.filter(User.id == user_id).delete()
    db_session.commit()
    flash('User deleted')
    return redirect(url_for('users'))


@flask_app.errorhandler(NotAuthorizedException)
def handle_no_result_exception(error):
    flash('Not authorized')
    return render_template('layout.html'), 401


@flask_app.errorhandler(401)
def handle_no_result_exception(error):
    flash('Not authorized')
    return render_template('layout.html'), 401


@flask_app.errorhandler(NoResultFound)
def handle_no_result_exception(error):
    flash('Item not found')
    return render_template('layout.html'), 404


@flask_app.errorhandler(404)
def page_not_found(e):
    flash(e)
    return render_template('layout.html'), 404


def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')


if __name__ == "__main__":
    flask_app.run(port=5111, host='0.0.0.0', static_files={'/static': '/path/to/static'})
