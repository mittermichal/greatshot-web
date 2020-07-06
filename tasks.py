import os
import subprocess
from urllib.parse import urlparse
import dramatiq
from dramatiq.brokers.redis import RedisBroker
import tasks_config
import requests
import glob
import sentry_sdk
import sentry_dramatiq

sentry_sdk.init(
    tasks_config.SENTRY_DSN,
    integrations=[sentry_dramatiq.DramatiqIntegration()],
)

redis_broker = RedisBroker(url=tasks_config.REDIS, middleware=[], namespace=tasks_config.DRAMATIQ_NS)
dramatiq.set_broker(redis_broker)


def get_worker_last_beat():
    return int(redis_broker.client.get('worker_last_beat').decode('utf-8'))


def set_render_status(url_parsed, render_id, status_msg, progress=0):
    print('render #{}: status: {} progress: {}'.format(render_id, status_msg, progress))
    requests.post(
        url_parsed.scheme + '://' + url_parsed.netloc + '/renders/'+str(render_id),
        json={'status_msg': status_msg, 'progress': progress},
        auth=(tasks_config.STREAMABLE_NAME, tasks_config.STREAMABLE_PW)
    )


def capture(start, end, etl=False, fps=50):
    # http://stackoverflow.com/questions/5069224/handling-subprocess-crash-in-windows
    if etl:
        open(tasks_config.ETPATH + 'etmain\\init-tga.cfg', 'w').write(
            'exec_at_time ' + str(int(end) - 500) + ' stopvideo')
        p = subprocess.Popen(['render-etl.bat', tasks_config.ETPATH])
    else:
        delete_screenshots('etpro')
        with open(os.path.join(tasks_config.ETPATH, 'etpro', 'record-tga.cfg'), 'w') as file:
            file.write('cl_avidemo '+str(fps))
        with open(os.path.join(tasks_config.ETPATH, 'etmain', 'init-tga.cfg'), 'w') as file:
            file.write('exec_at_time '+str(start)+' record-tga')
        with open(os.path.join(tasks_config.ETPATH, 'etmain', 'init-wav.cfg'), 'w') as file:
            file.write('exec_at_time '+str(start)+' record-wav')
        p = subprocess.Popen([os.path.join(tasks_config.ETPATH, 'ET.exe'),
                              '+set', 'cl_profile', 'merlin-stream',
                              '+set', 'com_ignorecrash', '1',
                              '+viewlog', '1', '+logfile', 'render.log'
                              '+set', 'fs_game', 'etpro', '+set com_maxfps 125',
                              '+timescale', '0', '+demo', 'demo-render',
                              '+timescale', '0', '+wait', '2',
                              '+timescale', '1', '+exec', 'init-tga',
                              '+condump', 'init-tga.log', '+timescale', '1',
                              '+set', 'nextdemo', 'exec preinit-wav'
                              ], cwd=tasks_config.ETPATH)
    try:
        p.communicate(timeout=60)
    except subprocess.TimeoutExpired as e:
        p.kill()
        raise e


def delete_screenshots(mod='etpro'):
    for file in glob.glob(os.path.join(tasks_config.ETPATH, mod+'/screenshots/*.tga')):
        os.remove(file)


def ffmpeg_args(name, country, crf, fps=50):
    args = ['ffmpeg', '-hide_banner', '-layouts', '-loglevel', 'warning', '-y', '-thread_queue_size', '256',
            '-framerate', str(fps), '-i', 'etpro/screenshots/shot%04d.tga']
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

    # test_progress(url_parsed, render_id)
    # return

    # download is finished too fast to set status
    set_render_status(url_parsed, render_id, 'downloading demo...', 5)
    demo_file_path = os.path.join(tasks_config.ETPATH, 'etpro/demos/demo-render.dm_84')
    r = requests.get(demo_url)
    if r.status_code == 200:
        open(demo_file_path, 'wb').\
            write(r.content)
    else:
        RenderException('error downloading cut demo')

    if os.stat(demo_file_path).st_size == 0:
        set_render_status(url_parsed, render_id, 'error: cut demo was empty', 100)
        raise RenderException('cut demo was empty')

    set_render_status(url_parsed, render_id, 'capturing screenshots and sound...', 10)
    try:
        capture(start, end, etl)
    except subprocess.TimeoutExpired:
        # this prob wont work as intended
        set_render_status(url_parsed, render_id, 'error: game capture took too long', 100)
        raise RenderException('game capture took too long')

    set_render_status(url_parsed, render_id, 'encoding video...', 40)
    if etl:
        args = ['ffmpeg', '-y', '-framerate', '60',
                '-i', 'C:\\Users\\admin\\Documents\\ETLegacy\\uvMovieMod\\videos\\render.avi',
                '-shortest', 'render.mp4']
    else:
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
        raise RenderException('Upload error: ' + str(r.status_code) + r.content.decode('utf-8'))


def test_progress(url_parsed, render_id):
    from time import sleep
    for i in range(0, 100, 20):
        set_render_status(url_parsed, render_id, 'p ' + str(i), i)
        sleep(2)
    set_render_status(url_parsed, render_id, 'finished', 100)


class RenderException(Exception):
    pass
