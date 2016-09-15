from pydblite.sqlite import Database, Table
import json

def get_player(players, i):
  for player in players:
    if player['bClientNum']==i:
      return player
  raise IndexError

def parse_infostring(str):
  ret = {}
  key=''
  for i,v in enumerate(str.split('\\')):
    if i%2:
      ret[key]=v
    else:
      key=v
  return ret


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
  #TODO: fix players[j['bAttacker']] out of bound
  for line in lines:
    j = json.loads(line.replace('\1', ''))
    if 'szType' in j and j['szType'] == 'player' and j['bTeam']<3:
      j['sprees'] = []
      j['spree'] = []
      j['hits'] = [0,0,0,0] #0,130,131,132
      players.append(j)
    if 'szType' in j and j['szType'] == 'obituary' and j['bAttacker'] != 254 and j['bAttacker'] != j['bTarget']:
      # and j['bAttacker']!=j['bTarget']:
      # if j['bAttacker']>=len(players):
      # print(j['bAttacker'])
      # print(players[j['bAttacker']])
      attacker = get_player(players,j['bAttacker'])
      spree = attacker['spree']
      sprees = attacker['sprees']
      if (not len(spree)) or (j['dwTime'] - spree[len(spree) - 1]['dwTime'] <= 4000):
        spree.append(j)
      else:
        if len(spree) >= 3:
          sprees.append(spree)
        spree = [j]
      attacker['spree'] = spree
      attacker['sprees'] = sprees

    if 'szType' in j and j['szType'] == 'bulletevent':
      attacker = get_player(players, j['bAttacker'])
      table.insert(int(j['bAttacker']), j['bRegion'])
      if j['bRegion']>0:
        reg=j['bRegion']-129
      else:
        reg=0
      attacker['hits'][reg]+=1
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