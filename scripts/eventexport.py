import os
import glob


class EventExport:
    # self.events=[]
    # last_event=None
    def __init__(self):
        self.events = []

    def add_event(self, time, msg):
        self.events.append({'time': time, 'msg': msg})
        return

    def export(self):
        # events[len(events)-1]['time']==time:
        # print(self.events)
        if not len(self.events):
            return
        for f in glob.glob("events/*.cfg"):
            os.remove(f)
        self.events.sort(key=lambda a: a['time'])
        last_time = -1
        prev_event = self.events[0]
        open('events/init.cfg', 'w').write(
            'exec_at_time ' + str(self.events[0]['time']) + ' events/' + str(self.events[0]['time']) + '\n')
        # open('events/'+str(self.events[0]['time'])+'.cfg','w').write('echo "'+ self.events[0]['msg'] +'"\nexec_at_time '+str(self.events[1]['time'])+' events/'+str(self.events[1]['time'])+'\n')
        for event in self.events:
            open('events/' + str(prev_event['time']) + '.cfg', 'w').write(
                'echo "' + prev_event['msg'] + '"\nexec_at_time ' + str(event['time']) + ' events/' + str(
                    event['time']) + '\n')
            prev_event = event
            # if event.time==last_time:

        return self.events


"""
exporter=EventExport()
exporter.add_event(50,"b")
exporter.add_event(100,"a")
exporter.add_event(150,"c")
exporter.export()
"""
