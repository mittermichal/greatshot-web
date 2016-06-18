from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import os
import subprocess
import urllib.request
import gamestv
import re
import json
from pydblite.pydblite import Base



app = Flask(__name__)
app.config.from_pyfile('config.cfg')

#http://flask.pocoo.org/docs/0.11/patterns/fileuploads/

def count_hits(lines):
  print(len(jfile))
  players=set()
  out=[]
  db = Base()
  db.create("player", "region")
  db.create_index("player")
  db.create_index("region")
  for line in lines:
    j=json.loads(line)
    if 'szType' in j and j['szType']=='bulletevent':
      db.insert(int(j['bAttacker']),int(j['bRegion']))
  db.cursor.execute('')

  print(db.cursor.fetchall())
  return [{'num':2}]


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in set(['tv_84','dm_84'])


def upload(request):
  if 'uselast' in request.form:
    print('uselast')
  elif request.form['matchId']!='' and request.form['map']!='':
    #print(re.findall('(\d+)',request.form['matchId'])[0])
    urllib.request.urlretrieve(gamestv.getDemosLinks(gamestv.getMatchDemosId( int(re.findall('(\d+)',request.form['matchId'])[0]) ))[int(request.form['map'])-1], 'upload/demo.tv_84')
    #print(gamestv.getDemosLinks(gamestv.getMatchDemosId(int(request.form['matchId']))))
  else:
    if 'file' not in request.files:
        #flash('No file part')
        return 'No file part'
    file = request.files['file']
    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
        #flash('No selected file')
        return 'No selected file'
    if not file or not allowed_file(file.filename):
        return 'bad extension'
    filename = 'demo.'+file.filename.rsplit('.', 1)[1]
    file.save(os.path.join('upload', filename))

@app.route('/cut', methods=['GET', 'POST'])
def cut():	
    if request.method == 'POST':
        upload(request)
        #CutDemo( PCHAR demoPath, PCHAR outFilePath, int start, int end, cutInfo_t type, int clientNum )
        subprocess.call([app.config['PARSERPATH'], 'cut', 'upload/demo.tv_84', 'download/demo-out.dm_84', request.form['start'], request.form['end'], request.form['cuttype'], request.form['clientnum']])
        #F:\Hry\et\hannes_ettv_demo_parser_tech3\Debug\Anders.Gaming.LibTech3.exe cut demo01-10-31.tv_84 demo01-10-31.dm_84 56621000 56632000 0
        return send_from_directory(directory='download', filename='demo-out.dm_84', as_attachment=True, attachment_filename='demo-out.dm_84')
        return 'ok'
        #return redirect(url_for('cut',filename='demo-out.dm_84'))
        #return 'upload ok'

    return render_template('cut.html')

@app.route('/export', methods=['GET', 'POST'])
def export():	
    if request.method == 'POST':
        upload(request)
        subprocess.call([ app.config['PARSERPATH'], 'indexer', app.config['INDEXER']])
        return render_template('export-out.html',out=open('download/out.json', 'r').read(),hits=count_hits(open('download/out.json', 'r').readlines()))
    return render_template('export.html')

if __name__ == "__main__":
    app.run(port=5111,host='0.0.0.0')
