from .db import db_session
from .models import Render
import dramatiq as drm
from dramatiq.brokers.redis import RedisBroker
import tasks_config

status_redis_broker = RedisBroker(url=tasks_config.REDIS+'/'+tasks_config.STATUS_WORKER_REDIS_DB, middleware=[])
drm.set_broker(status_redis_broker)


def get_worker_last_beat():
    return int(status_redis_broker.client.get('worker_last_beat').decode('utf-8'))


@drm.actor
def save_status(render_id, status_msg, progress=0):
    db_session.query(Render).filter(Render.id == render_id).update(
        {Render.status_msg: status_msg, Render.progress: progress}
    )
    db_session.commit()
    print(locals())

