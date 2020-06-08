import eventexport
import json



f = open('revives.json', 'r')
f.readline()
clientNum=8
data=[]
exporter=eventexport.EventExport()
#j = json.loads(f.readline())
for line in f.__iter__():
	j = json.loads(line)
	#j['persistant'] and not j['persistant'].__eq__(data)
	#com=diff(data,j['persistant'],j['clientNum'])
	try:
		if 'bRevived' in j and j['bReviver']==9 or j['bRevived']==9:
			exporter.add_event(j['dwTime']-500,str(j['bRevived'])+' '+str(j['dist']))
	except KeyError:
		continue


	#exporter.add_event()
exporter.export()
