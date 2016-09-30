#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, jsonify, flash
import os
import subprocess
import app.Libtech3
import urllib.request
from urllib.request import urlopen
import ftplib
import app.gamestv
import app.ftp
import re
from app.forms import ExportFileForm,ExportMatchLinkForm, CutForm, RenderForm
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
  if render.streamable_short!=None:
    return render_template('render.html', render=render)
  result = tasks.render.AsyncResult(render.celery_id)
  if request_wants_json():
    data = result.result or result.state
    #print(data)
    return jsonify(data)
  if result.successful():
    render.streamable_short = result.get()
    db_session.commit()
  return render_template('render.html', render = render)

@flask_app.route('/renders', methods=['GET', 'POST'])
def renders_list():
  if request.method == 'GET':
    renders = Render.query.order_by(desc(Render.id)).all()
    for render in renders:
      if render.streamable_short==None:
        result = tasks.render.AsyncResult(render.celery_id)
        if result.successful():
          render.streamable_short = result.get()
    db_session.commit()
    return render_template('render_list.html', renders = renders)
  if request.method == 'POST':
    form = RenderForm(request.form)
    filename = 'demo.tv_84'
    app.Libtech3.cut(flask_app.config['PARSERPATH'], 'upload/' + filename, 'download/demo-out.dm_84', str(int(request.form['start'])-2000),request.form['end'], request.form['cut_type'], request.form['client_num'])
    result = tasks.render.delay(flask_app.config['APPHOST']+'/download/demo-out.dm_84',request.form['start'],form.data['title'])
    r = Render(result.id,form.data['title'])
    db_session.add(r)
    db_session.flush()
    db_session.commit()
    return redirect(url_for('render_get', render_id=r.id))


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
      #return 'demo.tv_84'
      urllib.request.urlretrieve(
        app.gamestv.getDemosLinks(app.gamestv.getMatchDemosId(int(re.findall('(\d+)', request.form['matchId'])[0])))[
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
    app.Libtech3.cut(
      flask_app.config['PARSERPATH'], 'upload/' + filename, 'download/demo-out.dm_84', request.form['start'],
       request.form['end'], request.form['cut_type'], request.form['client_num'])
    return send_from_directory(directory='download', filename='demo-out.dm_84', as_attachment=True, attachment_filename='demo-out.dm_84')
  else:
    return render_template('cut.html', cut_form=cut_form, form1=form1, form2=form2)

#TODO export only POV events for dm_84 demo
@flask_app.route('/export', methods=['GET', 'POST'])
def export():
  form1, form2 = ExportFileForm(),ExportMatchLinkForm()
  if request.method == 'POST':
    cut_form = CutForm()
    rndr_form = RenderForm()
    if request.form['matchId'] != '' and request.form['map'] != '':
      try:
        return export_get(re.findall('(\d+)', request.form['matchId'])[0],request.form['map'])
      except Exception:
        print('404',request.form['map'])
    try:
      filename = upload(request)
    except Exception as e:
      flash("Didn't select map number.")
      return render_template('export.html', form1=form1, form2=form2)
    else:
      arg = flask_app.config['INDEXER'] % (filename)
      subprocess.call([flask_app.config['PARSERPATH'], 'indexer', arg ])
      if request.form['matchId'] != '' and request.form['map'] != '':
        export_save(re.findall('(\d+)', request.form['matchId'])[0], request.form['map'])
      return render_template('export-out.html', filename=filename, cut_form=cut_form, rndr_form=rndr_form, out=open('download/out.json', 'r').read(),
                           parser_out=parse_output(open('download/out.json', 'r').readlines()))
  return render_template('export.html',form1=form1, form2=form2)

@flask_app.route('/export/last')
def export_last():
  cut_form = CutForm()
  rndr_form = RenderForm()
  return render_template('export-out.html', cut_form=cut_form, rndr_form=rndr_form, out=open('download/out.json', 'r').read(),
                           parser_out=parse_output(open('download/out.json', 'r').readlines()))

def generate_ftp_path(export_id):
  path=''
  for c in export_id:
    path = path + c + '/'
  return path

@flask_app.route('/export/<export_id>/<map_num>')
def export_get(export_id,map_num):
  cut_form = CutForm()
  rndr_form = RenderForm()
  ftp_url='ftp://'+flask_app.config['FTP_USER']+':'+flask_app.config['FTP_PW']+'@'+flask_app.config['FTP_HOST']+'/exports/'+generate_ftp_path(export_id)+map_num+'.json'
  out=list(map(lambda x: x.decode('utf-8','replace'), urlopen(ftp_url).readlines()))
  return render_template('export-out.html', cut_form=cut_form, rndr_form=rndr_form, out="".join(out),
                           parser_out=parse_output(out))

def export_save(export_id,map):
  path='exports/'+generate_ftp_path(export_id)
  session = ftplib.FTP(flask_app.config['FTP_HOST'], flask_app.config['FTP_USER'], flask_app.config['FTP_PW'])
  app.ftp.chdir(session,path[:-1])
  file = open('download/out.json', 'rb')
  session.storbinary('STOR '+str(map)+'.json', file)
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

#TODO: upload raw video from worker
'''
@flask_app.route('/raw')
def raw():
  return send_from_directory(directory='.', filename='render.mp4', as_attachment=True, attachment_filename='render.mp4')
'''
if __name__ == "__main__":
  flask_app.run(port=5111, host='0.0.0.0')
