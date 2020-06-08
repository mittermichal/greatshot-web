import eventexport
import json

def diff(old,new):
	if new.__eq__(old) or not len(old):
		return None
	else:
		ret=""
		for i,v in enumerate(old):
			if v<new[i]:
				ret+=" ^2" + str(new[i])
			elif v>new[i]:
				ret += " ^1" + str(new[i])
			else:
				ret += " ^7" + str(v)
		return ret


f = open('F:\Hry\et\hannes_ettv_demo_parser_tech3\Debug\stats.json', 'r')
f.readline()
clientNum=8
data=[]
exporter=eventexport.EventExport()
j = json.loads(f.readline())
for line in f.__iter__():
	j = json.loads(line)
	#j['persistant'] and not j['persistant'].__eq__(data)
	#com=diff(data,j['persistant'],j['clientNum'])
	if j['persistant'] and not j['persistant'].__eq__(data) and j['clientNum']==8:
		#print(j['time'])
		com = diff(data, j['persistant'])
		if com!=None:
			exporter.add_event(j['time'],com)
		data=j['persistant']


	#exporter.add_event()
exporter.export()
