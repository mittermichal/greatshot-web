import os
import subprocess
import tasks_config
import requests
import urllib.request
import glob
import json
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from threading import Thread
from time import sleep, time
import status_worker

redis_broker = RedisBroker(url=tasks_config.REDIS)
dramatiq.set_broker(redis_broker)


def set_render_status(render_id, status_msg, progress=0):
    status_worker.save_status.send(render_id, status_msg, progress)
# redis_broker.client.set("render_status_{}".format(render_id),
#                         json.dumps({'status_msg': status_msg,
#                                     'progress': progress
#                                     })
#                         )


def get_render_status(render_id):
    try:
        status = redis_broker.client.get("render_status_{}".format(render_id))
        if status is not None:
            status_dict = json.loads(status.decode("utf-8"))
            status_dict['worker_last_beat'] = get_worker_last_beat()
            return status_dict
        else:
            return None

    except json.JSONDecodeError:
        return None


def capture(start, end, etl=False):
    # http://stackoverflow.com/questions/5069224/handling-subprocess-crash-in-windows
    if etl:
        open(tasks_config.ETPATH + 'etmain\\init-tga.cfg', 'w').write(
            'exec_at_time ' + str(int(end) - 500) + ' stopvideo')
        p = subprocess.Popen(['render-etl.bat', tasks_config.ETPATH])
    else:
        open(tasks_config.ETPATH + 'etmain\\init-tga.cfg', 'w').write('exec_at_time '+str(start)+' record-tga')
        open(tasks_config.ETPATH + 'etmain\\init-wav.cfg', 'w').write('exec_at_time '+str(start)+' record-wav')
        p = subprocess.Popen(['render.bat', tasks_config.ETPATH])
    p.communicate()


@dramatiq.actor
def render(render_id, demo_url, start, end, title='render', name='', country='', etl=False):
    print('download '+demo_url+' '+title)
    set_render_status(render_id, 'downloading demo...', 0)
    urllib.request.urlretrieve(demo_url, tasks_config.ETPATH+'etpro/demos/demo-render.dm_84')
    if os.stat(tasks_config.ETPATH+'etpro/demos/demo-render.dm_84').st_size == 0:
        # current_task.update_state(state='FAILURE')
        redis_broker.client.set("render_status_{}".format(render_id), 'received demo is empty')
        print("RENDER: received demo is empty")
        return None
    print('capture '+title)
    set_render_status(render_id, 'capturing screenshots and sound...', 5)
    capture(start, end, etl)

    print('encoding '+title)
    set_render_status(render_id, 'encoding video...', 30)
    if etl:
        args = ['ffmpeg', '-y', '-framerate', '60',
                '-i', 'C:\\Users\\admin\\Documents\\ETLegacy\\uvMovieMod\\videos\\render.avi',
                '-shortest', 'render.mp4']
    else:
        p = subprocess.check_output(['sox', 'etpro/wav/synctest.wav', '-n', 'stat', '2>&1'],
                                    cwd=tasks_config.ETPATH, shell=True).decode()
        len_s = p.find('Length') + 22
        audio_len = float(p[len_s:len_s + p[len_s:].find('Scaled') - 2])
        video_len = len(glob.glob(tasks_config.ETPATH+'etpro\\screenshots\\shot[0-9]*.tga'))/50
        print("audio_len:",  audio_len, "video_len", video_len)
        if audio_len == 0 or video_len == 0:
            # current_task.update_state(state='FAILURE')
            print("RENDER: video or audio is empty")
            return None
        # subprocess.check_output(['sox', 'etpro/wav/synctest.wav',
        # 'etpro/wav/sync.wav', 'tempo', str(audio_len/video_len)], cwd=tasks_config.ETPATH,shell=True)
        args = ['ffmpeg', '-y', '-framerate', '50', '-i', 'etpro/screenshots/shot%04d.tga',
                '-i', 'etpro/wav/synctest.wav', '-c:a', 'libvorbis', '-shortest', 'render.mp4']
    if name is not None and country is not None:
        if etl:
            args.insert(4, '-filter_complex')
            args.insert(5, "[0] overlay=25:25 [b]; [b] drawtext=fontfile=courbd.ttf:text='" +
                        name + "': fontcolor=white: fontsize=50: x=100: y=25+(60-text_h)/2")
            args.insert(4, '-i')
            args.insert(5, '4x3/'+country+'.png')
        else:
            args.insert(6, '-filter_complex')
            args.insert(7, "[0] [1] overlay=25:25 [b]; [b] drawtext=fontfile=courbd.ttf:text='" +
                        name + "': fontcolor=white: fontsize=50: x=100: y=25+45.0-text_h-5")
            args.insert(6, '-i')
            args.insert(7, '4x3/'+country+'.png')
    p = subprocess.Popen(args, cwd=tasks_config.ETPATH, shell=True)
    p.communicate()

    # https://api.streamable.com
    print('uploading '+title)
    set_render_status(render_id, 'uploading clip...', 50)
    # r = requests.post('https://api.streamable.com/upload',
    #                   auth=(tasks_config.STREAMABLE_NAME, tasks_config.STREAMABLE_PW),
    #                   files={'render.mp4': open(tasks_config.ETPATH+'render.mp4', 'rb')},
    #                   data={'title': title})

    try:
        set_render_status(render_id, 'finished', 100)
        return
        # return json.loads(r.text)["shortcode"]
    except KeyError:
        print('RENDER: failed to upload')
        # current_task.update_state(state='FAILURE')
        return None
    # return demoUrl


def get_worker_last_beat():
    return int(redis_broker.client.get('worker_last_beat').decode('utf-8'))


def send_beat():
    redis_broker.client.set('worker_last_beat', int(time()) * 1000)
    sleep(60)


# Thread(target=send_beat).start()
