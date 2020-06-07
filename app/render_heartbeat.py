from .status_worker import redis_broker
from time import sleep, time
from threading import Thread


def send_beat():
    redis_broker.client.set('worker_last_beat', int(time()) * 1000)
    print('sent heart beat')
    sleep(60)


Thread(target=send_beat).start()
