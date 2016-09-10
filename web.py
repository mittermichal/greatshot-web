#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import os
import subprocess
import app.Libtech3
import urllib.request
import gamestv
import re
from app.forms import ExportFileForm,ExportMatchLinkForm, CutForm
import markdown
import eventexport
import tasks
from app.db import db_session
from app.models import Render
from sqlalchemy import desc
from app.export import parse_output

flask_app = Flask(__name__)
flask_app.config.from_pyfile('config.cfg')


@flask_app.route('/renders/<render_id>')
def render_get(render_id):
	r = Render.query.filter(Render.id == render_id).first()
	return render_template('render.html', render = r)

@flask_app.route('/renders', methods=['GET', 'POST'])
def renders_list():
	if request.method == 'GET':
		renders = Render.query.order_by(desc(Render.id)).all()
		# print(result.id)
		for render in renders:
			result = tasks.render.AsyncResult(render.celery_id)
			if result.successful():
				render.streamable_short = result.get()
		return render_template('render_list.html', renders = renders)

	if request.method == 'POST':
		filename = 'demo.tv_84'
		app.Libtech3.cut(
			flask_app.config['PARSERPATH'], 'upload/' + filename, 'download/demo-out.dm_84', request.form['start'],
			request.form['end'], request.form['cut_type'], request.form['client_num'])
		result = tasks.render.delay(flask_app.config['APPHOST']+'/download/demo-out.dm_84')
		r = Render(result.id)
		db_session.add(r)
		db_session.flush()
		return redirect(url_for('render_get', render_id=r.id))


def spree_time_interval(spree):
	return {'start': spree[0]['dwTime'], 'end': spree[len(spree) - 1]['dwTime']}


@flask_app.teardown_appcontext
def shutdown_session(exception=None):
	db_session.remove()


'''
@flask_app.route('/render')
def render():
	if '127.0.0.1'!=request.remote_addr:
		return render_template('render.html',msg='rendering only available on localhost')
	# subprocess.Popen([app.config['ETPATH']+'et.exe', '+set fs_game etpro +demo gtv/demo-out +wait 150 +timescale 1 +cl_avidemo 60 +set nextdemo', "exec gtvsound" ], cwd=os.path.realpath(app.config['ETPATH']))
	# subprocess.Popen('ffmpeg -y -framerate 60 -i etpro\screenshots\shot%04d.tga -i etpro/wav/synctest.wav -c:a libvorbis -shortest render.mp4', cwd=os.path.realpath(app.config['ETPATH']))
	return render_template('render.html', renders = renders)
'''

def allowed_file(filename):
	return '.' in filename and \
	       filename.rsplit('.', 1)[1] in set(['tv_84', 'dm_84'])


# http://flask.pocoo.org/docs/0.11/patterns/fileuploads/
def upload(request):
	if 'uselast' in request.form:
		print('uselast')
	elif request.form['matchId'] != '' and request.form['map'] != '':
		urllib.request.urlretrieve(
			gamestv.getDemosLinks(gamestv.getMatchDemosId(int(re.findall('(\d+)', request.form['matchId'])[0])))[
				int(request.form['map']) - 1], 'upload/demo.tv_84')
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
	return send_from_directory(directory='download', filename=filename)

# TODO exclude POV playerstate/entity
@flask_app.route('/cut', methods=['GET', 'POST'])
def cut():
	form1, form2 = ExportFileForm(), ExportMatchLinkForm()
	cut_form = CutForm()
	if request.form.__contains__('start'):
		filename = upload(request)
		# CutDemo( PCHAR demoPath, PCHAR outFilePath, int start, int end, cutInfo_t type, int clientNum )
		app.Libtech3.cut(
			flask_app.config['PARSERPATH'], 'upload/' + filename, 'download/demo-out.dm_84', request.form['start'],
			 request.form['end'], request.form['cut_type'], request.form['client_num'])
		# F:\Hry\et\hannes_ettv_demo_parser_tech3\Debug\Anders.Gaming.LibTech3.exe cut demo01-10-31.tv_84 demo01-10-31.dm_84 56621000 56632000 0
		return send_from_directory(directory='download', filename='demo-out.dm_84', as_attachment=True, attachment_filename='demo-out.dm_84')
	else:
		return render_template('cut.html', cut_form=cut_form, form1=form1, form2=form2)


@flask_app.route('/export', methods=['GET', 'POST'])
def export():
	form1, form2 = ExportFileForm(),ExportMatchLinkForm()
	if request.method == 'POST':
		cut_form = CutForm()
		filename = upload(request)
		arg = flask_app.config['INDEXER'] % (filename)
		subprocess.call([flask_app.config['PARSERPATH'], 'indexer', arg ])
		return render_template('export-out.html', filename=filename, cut_form=cut_form, out=open('download/out.json', 'r').read(),
		                       parser_out=parse_output(open('download/out.json', 'r').readlines()))
	return render_template('export.html',form1=form1, form2=form2)

@flask_app.route('/export/last')
def export_last():
	cut_form = CutForm()
	return render_template('export-out.html', cut_form=cut_form, out=open('download/out.json', 'r').read(),
		                       parser_out=parse_output(open('download/out.json', 'r').readlines()))

@flask_app.route('/')
def index():
	return render_template('layout.html', msg=markdown.markdown(open('README.md', 'r').read()))


@flask_app.route('/matches', methods=['GET', 'POST'])
def matches():
	return render_template('layout.html', msg='soon™')


@flask_app.route('/players', methods=['GET', 'POST'])
def players():
	return render_template('layout.html', msg='soon™')

if __name__ == "__main__":
	flask_app.run(port=5111, host='0.0.0.0')
