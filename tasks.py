import os
import subprocess
import urllib.request
from urllib.parse import urlparse
import dramatiq
from dramatiq.brokers.redis import RedisBroker
import tasks_config
import requests

redis_broker = RedisBroker(url=tasks_config.REDIS, middleware=[], namespace=tasks_config.DRAMATIQ_NS)
dramatiq.set_broker(redis_broker)


def get_worker_last_beat():
    return int(redis_broker.client.get('worker_last_beat').decode('utf-8'))


def set_render_status(url_parsed, render_id, status_msg, progress=0):
    print('render #{}: status: {} progress: {}'.format(render_id, status_msg, progress))
    requests.post(
        url_parsed.scheme + '://' + url_parsed.netloc + '/renders/'+str(render_id),
        json={'status_msg': status_msg, 'progress': progress}
    )


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
    p.communicate(timeout=60)


def ffmpeg_args(name, country, crf):
    args = ['ffmpeg', '-hide_banner', '-y', '-framerate', '50', '-i', 'etpro/screenshots/shot%04d.tga']
    if name != "":
        args += [
            '-filter_complex',
            "[0] [1] overlay=25:150 [b]; [b] drawtext=fontfile=courbd.ttf:text='" +
            name + "': fontcolor=white: fontsize=50: x=100: y=150+45.0-text_h-5",
        ]
    if country != "None":
        args += ['-i', '4x3/' + country + '.png']
    args += ['-i', 'etpro/wav/synctest.wav', '-shortest', '-crf', str(crf), '-pix_fmt', 'yuv420p', 'render.mp4']
    return args


@dramatiq.actor(queue_name='render')
def render(render_id, demo_url, start, end, name=None, country=None, crf='23', etl=False):
    print(locals())
    url_parsed = urlparse(demo_url)

    # download is finished too fast to set status
    # set_render_status(render_id, 'downloading demo...', 5)
    set_render_status(url_parsed, render_id, 'capturing screenshots and sound...', 10)
    urllib.request.urlretrieve(demo_url, tasks_config.ETPATH+'etpro/demos/demo-render.dm_84')
    if os.stat(tasks_config.ETPATH+'etpro/demos/demo-render.dm_84').st_size == 0:
        set_render_status(url_parsed, render_id, 'error: cutted demo was empty', 100)
        return None
    try:
        capture(start, end, etl)
    except subprocess.TimeoutExpired:
        # this prob wont work as intended
        set_render_status(url_parsed, render_id, 'error: game capture took too long', 100)

    set_render_status(url_parsed, render_id, 'encoding video...', 40)
    if etl:
        args = ['ffmpeg', '-y', '-framerate', '60',
                '-i', 'C:\\Users\\admin\\Documents\\ETLegacy\\uvMovieMod\\videos\\render.avi',
                '-shortest', 'render.mp4']
    else:
        # p = subprocess.check_output(['sox', 'etpro/wav/synctest.wav', '-n', 'stat', '2>&1'],
        #                             cwd=tasks_config.ETPATH, shell=True).decode()
        # len_s = p.find('Length') + 22
        # audio_len = float(p[len_s:len_s + p[len_s:].find('Scaled') - 2])
        # video_len = len(glob.glob(tasks_config.ETPATH+'etpro\\screenshots\\shot[0-9]*.tga'))/50
        # print("audio_len:",  audio_len, "video_len", video_len)
        # if audio_len == 0 or video_len == 0:
        #     set_render_status(render_id, 'error: captured game video or audio is empty', 30)
        #     return None
        # subprocess.check_output(['sox', 'etpro/wav/synctest.wav',
        # 'etpro/wav/sync.wav', 'tempo', str(audio_len/video_len)], cwd=tasks_config.ETPATH,shell=True)
        args = ffmpeg_args(name, country, crf)

    p = subprocess.Popen(args, cwd=tasks_config.ETPATH, shell=True)
    p.communicate()
    set_render_status(url_parsed, render_id, 'uploading video', 90)
    filename = str(render_id) + '.mp4'
    # print(filename)
    # netloc = url_parsed.netloc.replace('localhost','127.0.0.1')
    # print('upload url: ' + url_parsed.scheme + '://' + url_parsed.netloc + '/upload')
    r = requests.put(
        url_parsed.scheme + '://' + url_parsed.netloc + '/renders',
        auth=(tasks_config.STREAMABLE_NAME, tasks_config.STREAMABLE_PW),
        files={filename: open(tasks_config.ETPATH + 'render.mp4', 'rb')})
    # print('upload r code:' + str(r.status_code))
    if r.status_code == 200:
        set_render_status(url_parsed, render_id, 'finished', 100)
    else:
        set_render_status(url_parsed, render_id, 'upload error', 100)
        print('upload error:', r.status_code, r.content)
