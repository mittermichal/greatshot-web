import os
import subprocess
from celery import Celery, current_task
import tasks_config
import requests
import urllib.request
import json

celery_app = Celery('tasks', broker=tasks_config.REDIS)
celery_app.conf.update(
    CELERY_RESULT_BACKEND=tasks_config.REDIS
)
celery_app.config_from_object("tasks_config")

def capture(start):
  open(tasks_config.ETPATH+'etpro\init-tga.cfg','w').write('exec_at_time '+start+' record-tga')
  open(tasks_config.ETPATH+'etpro\init-wav.cfg','w').write('exec_at_time '+start+' record-wav')

  p = subprocess.Popen( [ 'render.bat' , tasks_config.ETPATH ] )
  p.communicate()

@celery_app.task(name="render")
def render(demoUrl,start,title):
  print('download '+demoUrl+' '+title)
  current_task.update_state(state='PROGRESS', meta={'stage': 'downloading demo', 'i':0})
  urllib.request.urlretrieve( demoUrl, tasks_config.ETPATH+'etpro/demos/demo-render.dm_84')

  print('capture '+title)
  current_task.update_state(state='PROGRESS',meta={'stage': 'capturing screenshots and sound', 'i':5 })
  capture(start)

  print('encoding '+title)
  current_task.update_state(state='PROGRESS', meta={'stage': 'encoding video', 'i':30})
  p = subprocess.Popen(['ffmpeg', '-y', '-framerate', '60', '-i', 'etpro/screenshots/shot%04d.tga', '-i', 'etpro/wav/synctest.wav', '-c:a', 'libvorbis', '-shortest', 'render.mp4'],cwd=tasks_config.ETPATH, shell=True)
  p.communicate()

  #https://api.streamable.com
  print('uploading '+title)
  current_task.update_state(state='PROGRESS', meta={'stage': 'uploading clip...', 'i':50})
  #return 'aaaa'
  r=requests.post('https://api.streamable.com/upload', auth=(tasks_config.STREAMABLE_NAME, tasks_config.STREAMABLE_PW), files={'render.mp4': open(tasks_config.ETPATH+'render.mp4', 'rb')} , data = {'title':title})

  return json.loads(r.text)["shortcode"]
  #return demoUrl


if __name__ == '__main__':
  celery_app.start()