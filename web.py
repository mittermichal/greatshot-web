#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import os
import subprocess
import urllib.request
import gamestv
import re
import json
from pydblite.sqlite import Database, Table
from app.forms import ExportFileForm,ExportMatchLinkForm, CutForm
import eventexport

app = Flask(__name__)
app.config.from_pyfile('config.cfg')


def spree_time_interval(spree):
	return {'start': spree[0]['dwTime'], 'end': spree[len(spree) - 1]['dwTime']}


@app.route('/render')
def render():
	if '127.0.0.1'!=request.remote_addr:
		return render_template('render.html',msg='rendering only available on localhost')
	# subprocess.Popen([app.config['ETPATH']+'et.exe', '+set fs_game etpro +demo gtv/demo-out +wait 150 +timescale 1 +cl_avidemo 60 +set nextdemo', "exec gtvsound" ], cwd=os.path.realpath(app.config['ETPATH']))
	# subprocess.Popen('ffmpeg -y -framerate 60 -i etpro\screenshots\shot%04d.tga -i etpro/wav/synctest.wav -c:a libvorbis -shortest render.mp4', cwd=os.path.realpath(app.config['ETPATH']))
	'''p = subprocess.Popen(
		app.config['ETPATH'] + 'screenshots.bat',
		cwd=os.path.realpath(app.config['ETPATH']))
	p.communicate()'''
	return render_template('render.html')


# 131 - body or dead body(gibbing)
# 130 - head 
# 0 - target has spawnshield
# 132 teammate hit
def parse_output(lines):
	players = []
	db = Database(":memory:")
	table = db.create('hits', ("player", 'INTEGER'), ("region", 'INTEGER'))
	table.create_index("player")
	table.create_index("region")
	# exporter=eventexport.EventExport()
	for line in lines:
		j = json.loads(line)
		if 'szType' in j and j['szType'] == 'player':
			j['sprees'] = []
			j['spree'] = []
			players.append(j)
		if 'szType' in j and j['szType'] == 'obituary' and j['bAttacker'] != 254 and j['bAttacker'] != j['bTarget']:
			# and j['bAttacker']!=j['bTarget']:
			# if j['bAttacker']>=len(players):
			# print(j['bAttacker'])
			# print(players[j['bAttacker']])
			spree = players[j['bAttacker']]['spree']
			sprees = players[j['bAttacker']]['sprees']
			if (not len(spree)) or (j['dwTime'] - spree[len(spree) - 1]['dwTime'] <= 4000):
				spree.append(j)
			else:
				if len(spree) >= 3:
					sprees.append(spree)
				spree = [j]
			players[j['bAttacker']]['spree'] = spree
			players[j['bAttacker']]['sprees'] = sprees

		if 'szType' in j and j['szType'] == 'bulletevent':
			table.insert(int(j['bAttacker']), j['bRegion'])
		# if j['bAttacker']==int(player) and j['bRegion']!=130 and j['bRegion']!=131 and j['bRegion']!=0:
		# filter(lambda p: p['bClientNum'] == j['bTarget'], players)
		# exporter.add_event(j['dwTime'],'^2BULLETEVENT      ' +str(j['bRegion']) + '^7 ' + players[j['bTarget']]['szName'])
	# exporter.export()
	table.cursor.execute('SELECT player,region,count(*) FROM hits group by player,region')
	ret = []
	result = db.cursor.fetchall()
	for row in result:
		ret.append(list(row))
	# print(ret)
	return {'hits': ret, 'players': players}


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
			return 'No file part'
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


# TODO exclude POV playerstate/entity
@app.route('/cut')
def cut():
	form1, form2 = ExportFileForm(), ExportMatchLinkForm()
	cut_form = CutForm()
	if request.form.__contains__('start'):
		filename = upload(request)
		# CutDemo( PCHAR demoPath, PCHAR outFilePath, int start, int end, cutInfo_t type, int clientNum )
		subprocess.call(
			[app.config['PARSERPATH'], 'cut', 'upload/' + filename, 'download/demo-out.dm_84', request.form['start'],
			 request.form['end'], request.form['cut_type'], request.form['client_num']])
		# F:\Hry\et\hannes_ettv_demo_parser_tech3\Debug\Anders.Gaming.LibTech3.exe cut demo01-10-31.tv_84 demo01-10-31.dm_84 56621000 56632000 0
		# return send_from_directory(directory='download', filename='demo-out.dm_84', as_attachment=True, attachment_filename='demo-out.dm_84')
		return render()
	else:
		return render_template('cut.html', cut_form=cut_form, form1=form1, form2=form2)


@app.route('/export', methods=['GET', 'POST'])
def export():
	form1, form2 = ExportFileForm(),ExportMatchLinkForm()
	if request.method == 'POST':
		filename = upload(request)
		subprocess.call([app.config['PARSERPATH'], 'indexer', 'indexTarget/upload\\' + filename + app.config['INDEXER']])
		return render_template('export-out.html', out=open('download/out.json', 'r').read(),
		                       parser_out=parse_output(open('download/out.json', 'r').readlines()))
	return render_template('export.html',form1=form1, form2=form2)

@app.route('/export/last')
def export_last():
	return render_template('export-out.html', out=open('download/out.json', 'r').read(),
		                       parser_out=parse_output(open('download/out.json', 'r').readlines()))

@app.route('/')
def index():
	return render_template('layout.html', msg='hello')


@app.route('/matches', methods=['GET', 'POST'])
def matches():
	return render_template('layout.html', msg='soon™')


@app.route('/players', methods=['GET', 'POST'])
def players():
	return render_template('layout.html', msg='soon™')


if __name__ == "__main__":
	app.run(port=5111, host='localhost')
