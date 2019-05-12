import os
import subprocess
from celery import Celery, current_task
import tasks_config
import requests
import urllib.request
import glob
import json

os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

celery_app = Celery('tasks', broker=tasks_config.REDIS)
celery_app.conf.update(
    CELERY_RESULT_BACKEND=tasks_config.REDIS,
    BROKER_URL=tasks_config.REDIS
)
celery_app.config_from_object("tasks_config")

def capture(start,end,etl=False):
  #http://stackoverflow.com/questions/5069224/handling-subprocess-crash-in-windows
  if etl:
    open(tasks_config.ETPATH + 'etmain\init-tga.cfg', 'w').write(
      'exec_at_time ' + str(int(end) - 500) + ' stopvideo')
    p = subprocess.Popen(['render-etl.bat', tasks_config.ETPATH])
  else:
    open(tasks_config.ETPATH+'etmain\init-tga.cfg','w').write('exec_at_time '+str(start)+' record-tga')
    open(tasks_config.ETPATH+'etmain\init-wav.cfg','w').write('exec_at_time '+str(start)+' record-wav')
    p = subprocess.Popen( [ 'render.bat' , tasks_config.ETPATH ] )
  p.communicate()

@celery_app.task(name="render")
def render(demoUrl,start,end,title='render',name='',country='',etl=False):
  print('download '+demoUrl+' '+title)
  current_task.update_state(state='PROGRESS', meta={'stage': 'downloading demo', 'i':0})
  urllib.request.urlretrieve( demoUrl, tasks_config.ETPATH+'etpro/demos/demo-render.dm_84')
  if os.stat(tasks_config.ETPATH+'etpro/demos/demo-render.dm_84').st_size==0:
      current_task.update_state(state='FAILURE')
      return None
  print('capture '+title)
  current_task.update_state(state='PROGRESS',meta={'stage': 'capturing screenshots and sound', 'i':5 })
  capture(start,end,etl)

  print('encoding '+title)
  current_task.update_state(state='PROGRESS', meta={'stage': 'encoding video', 'i':30})
  if etl:
    args = ['ffmpeg', '-y', '-framerate', '60', '-i', 'C:\\Users\\admin\\Documents\\ETLegacy\\uvMovieMod\\videos\\render.avi', '-shortest', 'render.mp4']
  else:
    p = subprocess.check_output(['sox', 'etpro/wav/synctest.wav', '-n', 'stat', '2>&1'], cwd=tasks_config.ETPATH, shell=True).decode()
    len_s = p.find('Length') + 22
    audio_len=float(p[len_s:len_s + p[len_s:].find('Scaled') - 2])
    video_len=len(glob.glob(tasks_config.ETPATH+'etpro\\screenshots\shot[0-9]*.tga'))/50
    print("audio_len:",  audio_len, "video_len", video_len)
    if audio_len==0 or video_len==0:
      current_task.update_state(state='FAILURE')
      return None
    # subprocess.check_output(['sox', 'etpro/wav/synctest.wav', 'etpro/wav/sync.wav', 'tempo', str(audio_len/video_len)], cwd=tasks_config.ETPATH,shell=True)
    args = ['ffmpeg', '-y', '-framerate', '50', '-i', 'etpro/screenshots/shot%04d.tga', '-i', 'etpro/wav/synctest.wav', '-c:a', 'libvorbis', '-shortest', 'render.mp4']
  if name!=None and country!=None:
    if etl:
      args.insert(4,'-filter_complex')
      args.insert(5,"[0] overlay=25:25 [b]; [b] drawtext=fontfile=courbd.ttf:text='"+name+"': fontcolor=white: fontsize=50: x=100: y=25+(60-text_h)/2")
      args.insert(4, '-i')
      args.insert(5, '4x3/'+country+'.png')
    else:
      args.insert(6,'-filter_complex')
      args.insert(7,"[0] [1] overlay=25:25 [b]; [b] drawtext=fontfile=courbd.ttf:text='"+name+"': fontcolor=white: fontsize=50: x=100: y=25+45.0-text_h-5")
      args.insert(6, '-i')
      args.insert(7, '4x3/'+country+'.png')
  p = subprocess.Popen(args,cwd=tasks_config.ETPATH, shell=True)
  p.communicate()

  #https://api.streamable.com
  print('uploading '+title)
  current_task.update_state(state='PROGRESS', meta={'stage': 'uploading clip...', 'i':50})
  #return 'aaaa'
  r=requests.post('https://api.streamable.com/upload', auth=(tasks_config.STREAMABLE_NAME, tasks_config.STREAMABLE_PW), files={'render.mp4': open(tasks_config.ETPATH+'render.mp4', 'rb')} , data = {'title':title})

  try:
    return json.loads(r.text)["shortcode"]
  except Exception:
    current_task.update_state(state='FAILURE')
    return None
  #return demoUrl


if __name__ == '__main__':
  celery_app.start()