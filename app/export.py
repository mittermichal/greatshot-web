from pydblite.sqlite import Database, Table
import json

# 131 - body or dead body(gibbing)
# 130 - head
# 0 - target has spawnshield
# 132 teammate hit
def parse_output(lines):
	players = []
	db = Database(":memory:")
	table = db.create('hits', ("player", 'INTEGER'), ("region", 'INTEGER'))
	table.create_index("player")
	table.create_index("region")
	# exporter=eventexport.EventExport()
	for line in lines:
		j = json.loads(line.replace('\1', ''))
		if 'szType' in j and j['szType'] == 'player':
			j['sprees'] = []
			j['spree'] = []
			players.append(j)
		if 'szType' in j and j['szType'] == 'obituary' and j['bAttacker'] != 254 and j['bAttacker'] != j['bTarget']:
			# and j['bAttacker']!=j['bTarget']:
			# if j['bAttacker']>=len(players):
			# print(j['bAttacker'])
			# print(players[j['bAttacker']])
			spree = players[j['bAttacker']]['spree']
			sprees = players[j['bAttacker']]['sprees']
			if (not len(spree)) or (j['dwTime'] - spree[len(spree) - 1]['dwTime'] <= 4000):
				spree.append(j)
			else:
				if len(spree) >= 3:
					sprees.append(spree)
				spree = [j]
			players[j['bAttacker']]['spree'] = spree
			players[j['bAttacker']]['sprees'] = sprees

		if 'szType' in j and j['szType'] == 'bulletevent':
			table.insert(int(j['bAttacker']), j['bRegion'])
		# if j['bAttacker']==int(player) and j['bRegion']!=130 and j['bRegion']!=131 and j['bRegion']!=0:
		# filter(lambda p: p['bClientNum'] == j['bTarget'], players)
		# exporter.add_event(j['dwTime'],'^2BULLETEVENT      ' +str(j['bRegion']) + '^7 ' + players[j['bTarget']]['szName'])
	# exporter.export()
	table.cursor.execute('SELECT player,region,count(*) FROM hits group by player,region')
	ret = []
	result = db.cursor.fetchall()
	for row in result:
		ret.append(list(row))
	# print(ret)
	return {'hits': ret, 'players': players}