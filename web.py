from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import os
import subprocess
import urllib.request
import gamestv
import re
import json
from pydblite.sqlite import Database, Table



app = Flask(__name__)
app.config.from_pyfile('config.cfg')

#http://flask.pocoo.org/docs/0.11/patterns/fileuploads/

def count_hits(lines):
  players=set()
  out=[]
  db = Database(":memory:")
  table = db.create('hits', ("player",'INTEGER'), ("region",'INTEGER'))
  table.create_index("player")
  table.create_index("region")
  for line in lines:
    j=json.loads(line)
    if 'szType' in j and j['szType']=='bulletevent':
      table.insert(int(j['bAttacker']),int(j['bRegion']))
  table.cursor.execute('SELECT player,region,count(*) FROM hits group by player,region')
  ret = []
  result = db.cursor.fetchall()
  for row in result:
    ret.append(list(row))
  print(ret)
  return ret
  #[(0, 0, 14), (0, 130, 18), (0, 131, 177), (0, 132, 1), (1, 0, 5), (1, 130, 34),...
  return [{'num':2}]


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in set(['tv_84','dm_84'])

def upload(request):
  if 'uselast' in request.form:
    print('uselast')
  elif request.form['matchId']!='' and request.form['map']!='':
    urllib.request.urlretrieve(gamestv.getDemosLinks(gamestv.getMatchDemosId( int(re.findall('(\d+)',request.form['matchId'])[0]) ))[int(request.form['map'])-1], 'upload/demo.tv_84')
  else:
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
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
        #subprocess.call([ app.config['PARSERPATH'], 'indexer', app.config['INDEXER']])
        return render_template('export-out.html',out=open('download/out.json', 'r').read(),hits=count_hits(open('download/out.json', 'r').readlines()))
    return render_template('export.html')

if __name__ == "__main__":
    app.run(port=5111,host='0.0.0.0')
