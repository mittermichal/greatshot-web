import os
import subprocess
from celery import Celery
import tasks_config
import requests
import urllib.request

celery_app = Celery('tasks', broker=tasks_config.REDIS)
celery_app.conf.update(
    CELERY_RESULT_BACKEND=tasks_config.REDIS
)
celery_app.config_from_object("tasks_config")

@celery_app.task(name="render")
def render(demoUrl):

  #download demoUrl
  urllib.request.urlretrieve( demoUrl, tasks_config.ETPATH+'etpro/demos/demo-render.dm_84')

  p = subprocess.Popen( [ 'render.bat' , tasks_config.ETPATH ] )
  p.communicate()
  #https://api.streamable.com/upload
  #r=requests.post('https://api.streamable.com/upload', auth=(tasks_config.STREAMABLE_NAME, tasks_config.STREAMABLE_PW), files={'render.mp4': open('render.mp4', 'rb')})
  #return r.text["shortcode"]
  return demoUrl


if __name__ == '__main__':
  celery_app.start()