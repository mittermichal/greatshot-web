import sqlite3
import json
from math import sqrt
from sqlalchemy import desc
from app.models import Render
from app.game import game as game_module


def get_player(players, i):
    for player in players:
        if player['bClientNum'] == i:
            return player
    raise IndexError


def parse_config_string(config_string):
    ret = {}
    key = ''
    for i, v in enumerate(config_string.split('\\')[1:]):
        if i % 2:
            ret[key] = v
        else:
            key = v
    return ret


def dist(x1, y1, x2, y2):
    return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))


# 131 - body or dead body(gibbing)
# 130 - head
# 0 - target has spawnshield
# 132 teammate hit
def parse_output(lines, spree_timeout, hs_spree_timeout, gtv_match_id=None, map_num=None):
    players = []
    rounds = []
    chat = []
    demo = {}
    moment_builder = MomentBuilder(gtv_match_id, map_num)

    db = sqlite3.connect(':memory:')
    db.execute('''CREATE TABLE hits
                 (player INTEGER, region INTEGER, time INTEGER, weapon INTEGER)''')
    db.execute("CREATE INDEX p ON hits(player)")
    db.execute("CREATE INDEX r ON hits(region)")
    db.execute("CREATE INDEX w ON hits(weapon)")
    db.execute("CREATE INDEX t ON hits(time)")


    # if gtv_match_id is not None and gtv_match_id != '':
    #     g_players = app.gamestv.getPlayers(gtv_match_id)
    # else:
    #     g_players = []

    # exporter=eventexport.EventExport()
    # TODO: fix players[j['bAttacker']] out of bound

    mod = None
    mod_version = None
    protocol = None
    game = None
    config_string = None

    for line in lines:
        # print(line.decode('utf-8'))
        if type(line) is bytes:
            line = line.decode('utf-8', 'replace')
        j = json.loads(line.replace('\1', ''), strict=False)

        if 'szType' in j and j['szType'] == 'demo':
            demo = j
            config_string = parse_config_string(demo['szServerConfig'])
            mod = config_string['gamename']
            # mod_version = config_string['mod_version']
            # protocol = config_string['protocol']
            game = game_module.Game.by_mod(mod)()

        elif 'szType' in j and j['szType'] == 'round':
            j['szEndRoundStats'] = j['szEndRoundStats'].replace('%n', '\n')
            rounds.append(j)

        elif 'szType' in j and j['szType'] == 'player':
            j['sprees'] = []
            j['spree'] = []
            j['revives'] = 0
            j['revived'] = 0
            j['rifletricks'] = []
            j['hits'] = {region.name: 0 for region in game.regions}  # 0,130,131,132

            j['hs_sprees'] = []
            j['hs_spree'] = []

            players.append(j)

        elif 'szType' in j and j['szType'] == 'obituary' and j['bAttacker'] != 254 and j['bAttacker'] != j[
            'bTarget'] and j['bIsTeamkill'] == 0:
            # and j['bAttacker']!=j['bTarget']:
            # if j['bAttacker']>=len(players):
            # print(j['bAttacker'])
            # print(players[j['bAttacker']])

            attacker = get_player(players, j['bAttacker'])
            if all([key in j for key in ['kx', 'ky', 'tx', 'ty']]):
                j['distance'] = dist(j['kx'], j['ky'], j['tx'], j['ty'])
                # riflenade
                if mod == 'etpro':
                    if (j['bWeapon'] == 43 or j['bWeapon'] == 44) and j['distance'] > 2000:
                        attacker['rifletricks'].append(moment_builder.build('rifletrick', [j]))

            spree = attacker['spree']
            sprees = attacker['sprees']
            if (not len(spree)) or (j['dwTime'] - spree[len(spree) - 1]['dwTime'] <= spree_timeout):
                spree.append(j)
            else:
                if len(spree) >= 3:
                    sprees.append(moment_builder.build('spree', spree))
                spree = [j]
            attacker['spree'] = spree
            attacker['sprees'] = sprees

        elif 'szType' in j and j['szType'] == 'bulletevent':
            j['weapon'] = game.weapons(j['bWeapon']).name
            attacker = get_player(players, j['bAttacker'])
            if game.is_headshot(j['bRegion']):
                hs_spree = attacker['hs_spree']
                hs_sprees = attacker['hs_sprees']
                if (not len(hs_spree)) or (j['dwTime'] - hs_spree[len(hs_spree) - 1]['dwTime'] <= hs_spree_timeout):
                    hs_spree.append(j)
                else:
                    if len(hs_spree) >= 3:
                        hs_sprees.append(moment_builder.build('hs_spree', hs_spree))
                    hs_spree = [j]
                attacker['hs_spree'] = hs_spree
                attacker['hs_sprees'] = hs_sprees

            # table.insert(int(j['bAttacker']), j['bRegion'], j['dwTime'], j['bWeapon'])
            db.execute("INSERT INTO hits VALUES (?,?,?,?)", (int(j['bAttacker']), j['bRegion'], j['dwTime'], j['bWeapon']))
            attacker['hits'][game.regions(j['bRegion']).name] += 1
        elif 'szType' in j and j['szType'] == 'revive':
            try:
                reviver = get_player(players, j['bReviver'])
            except IndexError:
                continue
            else:
                reviver['revives'] = reviver['revives'] + 1
            revived = get_player(players, j['bRevived'])
            revived['revived'] = revived['revived'] + 1
        elif 'szType' in j and j['szType'] == 'chat' and j["bPlayer"] != -1:
            chat.append(j)
    for player in players:
        if len(player['spree']) >= 3:
            player['sprees'].append(moment_builder.build('kill_spree', player['spree']))
        if len(player['hs_spree']) >= 3:
            player['hs_sprees'].append(moment_builder.build('hs_spree', player['hs_spree']))
        player['has_hits'] = any(player['hits'][region] > 0 for region in player['hits'])

        for spree in player['sprees']:
            sql = '''SELECT region,weapon,count(*) as c FROM hits 
            WHERE player=? and time>? and time<? group by region,weapon
            '''
            rows = db.execute(sql, (
                player['bClientNum'],
                spree.render_start(),
                spree.render_end()
            ))
            spree.hit_summary = {'{}-{}'.format(game.regions(row[0]).name, game.weapons(row[1]).name): row[2]
                                 for row in rows}

        # if j['bAttacker']==int(player) and j['bRegion']!=130 and j['bRegion']!=131 and j['bRegion']!=0:
        # filter(lambda p: p['bClientNum'] == j['bTarget'], players)
        # exporter.add_event(j['dwTime'],'^2BULLETEVENT      ' +str(j['bRegion']) + '^7 ' + players[j['bTarget']]['szName'])
    # exporter.export()
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
    return {
        'hit_regions': [region.name for region in game.regions],
        # 'hits': ret,
        'players': players,
        'demo': demo,
        'rounds': rounds,
        'chat': chat,
        'mod': mod,
        'isETTV': 'ETTV' == config_string['version'][:4]
    }


class MomentBuilder:
    def __init__(self, gtv_match_id, map_num):
        self.gtv_match_id = gtv_match_id
        self.map_num = map_num

    def build(self, moment_type, j):
        return Moment(moment_type, j, self.gtv_match_id, self.map_num)


class Moment:
    def __init__(self, type, jsons, gtv_match_id, map_num):
        self.type = type
        self.jsons = jsons
        self.renders = []
        self.gtv_match_id = gtv_match_id
        self.map_num = map_num
        self.renders_count = 0
        self.find_renders()
        self.hit_summary = {}

    def find_renders(self):
        if self.gtv_match_id is not None and self.gtv_match_id != '':
            self.renders = Render.query.order_by(desc(Render.id))\
                .filter(
                    Render.gtv_match_id == self.gtv_match_id,
                    Render.map_number == self.map_num,
                    Render.client_num == self.jsons[0]['bAttacker'],
                    Render.start <= self.start(),
                    Render.end >= self.end(),
                )
            self.renders_count = self.renders.count()

    def start(self):
        return self.jsons[0]['dwTime']

    def end(self):
        return self.jsons[len(self.jsons) - 1]['dwTime']

    def render_start(self):
        if self.type == 'rifletrick':
            margin = 6000
        else:
            margin = 3000
        return self.start() - margin

    def render_end(self):
        return self.end() + 2000

    def render_length(self):
        return self.render_end() - self.render_start()

    def size(self):
        return len(self.jsons)

    def length(self):
        return self.jsons[len(self.jsons) - 1]['dwTime']-self.jsons[0]['dwTime']


class ModNotSupported(Exception):
    def __init__(self, mod: str):
        self.mod = mod
