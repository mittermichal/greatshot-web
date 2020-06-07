import os
import subprocess
import urllib.request
import glob
import dramatiq
from dramatiq.brokers.redis import RedisBroker
import tasks_config
from app.status_worker import save_status

redis_broker = RedisBroker(url=tasks_config.REDIS+'/0', middleware=[])
dramatiq.set_broker(redis_broker)


def set_render_status(render_id, status_msg, progress=0):
    print('render #{}: status: {} progress: {}'.format(render_id, status_msg, progress))
    save_status.send(render_id, status_msg, progress)


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
    # download is finished too fast to set status
    # set_render_status(render_id, 'downloading demo...', 5)
    urllib.request.urlretrieve(demo_url, tasks_config.ETPATH+'etpro/demos/demo-render.dm_84')
    if os.stat(tasks_config.ETPATH+'etpro/demos/demo-render.dm_84').st_size == 0:
        # current_task.update_state(state='FAILURE')
        set_render_status(render_id, 'error: cutted demo was empty', 100)
        return None
    set_render_status(render_id, 'capturing screenshots and sound...', 10)
    capture(start, end, etl)

    set_render_status(render_id, 'encoding video...', 40)
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
            set_render_status(render_id, 'error: captured game video or audio is empty', 30)
            return None
        # subprocess.check_output(['sox', 'etpro/wav/synctest.wav',
        # 'etpro/wav/sync.wav', 'tempo', str(audio_len/video_len)], cwd=tasks_config.ETPATH,shell=True)
        args = ['ffmpeg', '-hide_banner', '-v', 'warning', '-y', '-framerate', '50', '-i', 'etpro/screenshots/shot%04d.tga']
    if name is not None and country is not None:
        args += [
            '-filter_complex',
            "[0] [1] overlay=25:25 [b]; [b] drawtext=fontfile=courbd.ttf:text='" +
            name + "': fontcolor=white: fontsize=50: x=100: y=25+45.0-text_h-5",
            '-i',
            '4x3/'+country+'.png'
        ]
    args += ['-i', 'etpro/wav/synctest.wav', '-c:a', 'libvorbis', '-shortest', 'render.mp4']
    # print(args)
    p = subprocess.Popen(args, cwd=tasks_config.ETPATH, shell=True)
    p.communicate()

    # https://api.streamable.com
    # set_render_status(render_id, 'uploading clip...', 80)
    # r = requests.post('https://api.streamable.com/upload',
    #                   auth=(tasks_config.STREAMABLE_NAME, tasks_config.STREAMABLE_PW),
    #                   files={'render.mp4': open(tasks_config.ETPATH+'render.mp4', 'rb')},
    #                   data={'title': title})

    try:
        set_render_status(render_id, 'finished', 100)
        return
        # return json.loads(r.text)["shortcode"]
    except KeyError:
        set_render_status(render_id, 'error: failed to upload to streamable', 100)
        return None
    # return demoUrl
