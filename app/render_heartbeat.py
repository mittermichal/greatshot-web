from tasks import redis_broker
from time import sleep, time
from threading import Thread


def send_beat():
    while True:
        redis_broker.client.set('worker_last_beat', redis_broker.client.time()[0])
        # print('sent heart beat')
        sleep(60)


Thread(target=send_beat).start()
