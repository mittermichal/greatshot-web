from app.db import db_session
from app.models import Render
import requests


def dl_streamable(streamable_short, render_id='test'):
    api = 'https://api.streamable.com/videos/'
    r = requests.get(api + streamable_short)
    if r.status_code == 200:
        file_url = 'https:'+r.json()['files']['mp4']['url']
        print('dl video...')
        rv = requests.get(file_url)
        open('app/download/renders/'+str(render_id)+'.mp4', 'wb').write(rv.content)
    else:
        print(render_id, r.status_code)


for render in db_session.query(Render).filter(Render.streamable_short != None):
    dl_streamable(render.streamable_short, render.id)
