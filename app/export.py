from pydblite.sqlite import Database, Table
import json
from math import sqrt
from app.forms import PlayerForm
import app.gamestv

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

def dist(x1,y1,x2,y2):
  return sqrt( pow(x1-x2,2) + pow(y1-y2,2))

# 131 - body or dead body(gibbing)
# 130 - head
# 0 - target has spawnshield
# 132 teammate hit
def parse_output(lines,gtv_match_id=None):
  players = []
  rounds = []
  chat = []
  demo = {}
  db = Database(":memory:")
  table = db.create('hits', ("player", 'INTEGER'), ("region", 'INTEGER'))
  table.create_index("player")
  table.create_index("region")

  if gtv_match_id!=None and gtv_match_id!='':
    g_players = app.gamestv.getPlayers(gtv_match_id)
  else:
    g_players = []

  # exporter=eventexport.EventExport()
  #TODO: fix players[j['bAttacker']] out of bound
  for line in lines:
    #print(line.decode('utf-8'))
    if type(line) is bytes:
      line=line.decode('utf-8','replace')
    j = json.loads(line.replace('\1', ''),strict=False)
    if 'szType' in j and j['szType'] == 'demo':
      demo = j

    elif 'szType' in j and j['szType'] == 'round':
      j['szEndRoundStats']=j['szEndRoundStats'].replace('%n','\n')
      rounds.append(j)

    elif 'szType' in j and j['szType'] == 'player':
      j['sprees'] = []
      j['spree'] = []
      j['revives'] = 0
      j['revived'] = 0
      j['rifletricks'] = []
      j['hits'] = [0,0,0,0] #0,130,131,132

      j['hs_sprees'] = []
      j['hs_spree'] = []

      form = PlayerForm()
      form.client_num.data = j['bClientNum']
      if gtv_match_id!=None:

        for g_player in g_players:
          if j['szCleanName'].lower().find(g_player['name'].lower())!=-1:
            form.name.data=g_player['name']
            form.country.data = g_player['country']


      j['form'] = form
      players.append(j)

    elif 'szType' in j and j['szType'] == 'obituary' and j['bAttacker'] != 254 and j['bAttacker'] != j['bTarget'] and j['bIsTeamkill']==0:
      # and j['bAttacker']!=j['bTarget']:
      # if j['bAttacker']>=len(players):
      # print(j['bAttacker'])
      # print(players[j['bAttacker']])

      attacker = get_player(players, j['bAttacker'])
      j['distance']=dist(j['kx'],j['ky'],j['tx'],j['ty'])

      #riflenade
      if (j['bWeapon']==43 or j['bWeapon']==44) and j['distance']>2000:
        attacker['rifletricks'].append(j)

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

    elif 'szType' in j and j['szType'] == 'bulletevent':
      attacker = get_player(players, j['bAttacker'])
      if j['bRegion']==130:
        hs_spree = attacker['hs_spree']
        hs_sprees = attacker['hs_sprees']
        if (not len(hs_spree)) or (j['dwTime'] - hs_spree[len(hs_spree) - 1]['dwTime'] <= 4000):
          hs_spree.append(j)
        else:
          if len(hs_spree) >= 3:
            hs_sprees.append(hs_spree)
          hs_spree = [j]
        attacker['hs_spree'] = hs_spree
        attacker['hs_sprees'] = hs_sprees

      table.insert(int(j['bAttacker']), j['bRegion'])
      if j['bRegion']>0:
        reg=j['bRegion']-129
      else:
        reg=0
      attacker['hits'][reg]+=1
    elif 'szType' in j and j['szType'] == 'revive':
      try:
        reviver = get_player(players, j['bReviver'])
      except IndexError:
        continue
      else:
        reviver['revives'] = reviver['revives'] + 1
      revived = get_player(players, j['bRevived'])
      revived['revived']=revived['revived']+1
    elif 'szType' in j and j['szType'] == 'chat' and j["bPlayer"] != -1:
      chat.append(j)

    # if j['bAttacker']==int(player) and j['bRegion']!=130 and j['bRegion']!=131 and j['bRegion']!=0:
    # filter(lambda p: p['bClientNum'] == j['bTarget'], players)
    # exporter.add_event(j['dwTime'],'^2BULLETEVENT      ' +str(j['bRegion']) + '^7 ' + players[j['bTarget']]['szName'])
  # exporter.export()
  table.cursor.execute('SELECT player,region,count(*) FROM hits group by player,region')
  ret = []
  result = db.cursor.fetchall()
  for row in result:
    ret.append(list(row))
  """
  TODO: player db
  if gtv_match_id!=None:
    for player in players:
      mp = MatchPlayer.query.filter(MatchPlayer.gtv_match_id == gtv_match_id,MatchPlayer.client_num == player['bClientNum']).first()
      if mp!=None:
        db_player=Player.query.filter(Player.id == mp.player_id).first()
        player['id'] = db_player.id
        player['name'] = db_player.name
        player['country']= db_player.country
      else:
        player['name'] = None
  """
  return {'hits': ret, 'players': players, 'demo': demo, 'rounds' : rounds, 'g_players': g_players, 'chat': chat}