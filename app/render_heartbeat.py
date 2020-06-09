from tasks import tasks_redis_broker
from time import sleep, time
from threading import Thread


def send_beat():
    while True:
        tasks_redis_broker.client.set('worker_last_beat', tasks_redis_broker.client.time()[0])
        # print('sent heart beat')
        sleep(60)


Thread(target=send_beat).start()
