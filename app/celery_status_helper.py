from celery import Celery
from .. import tasks_config

if __name__ == '__main__':
    celery_app = Celery(broker=tasks_config.REDIS)
    celery_app.conf.update(
        CELERY_RESULT_BACKEND=tasks_config.REDIS
    )
    celery_app.config_from_object("tasks_config")
    return celery_app.control.inspect().stats()
