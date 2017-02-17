import urllib
from urllib.request import HTTPError,URLError
from flask import Flask
import web
import app.gamestv
import subprocess
from app.models import Render

flask_app = Flask(__name__)
flask_app.config.from_pyfile('config.cfg')

def process_match(match_id,render=True):
  hs=''
  for map_num,demo_url in enumerate(app.gamestv.getDemosLinks(app.gamestv.getMatchDemosId(match_id))):
    try:
      parser_out = web.export_get(str(match_id),str(map_num),False,False)
    except (HTTPError,URLError):
      print('not on ftp')
      urllib.request.urlretrieve(demo_url, 'upload/demo.tv_84')
      #except HTTPError:
      arg = flask_app.config['INDEXER'] % ('demo.tv_84')
      subprocess.call([flask_app.config['PARSERPATH'], 'indexer', arg])
      try:
        web.export_save(str(match_id), map_num)
      except TimeoutError:
        print("ftp timeout")
      parser_out = web.parse_output(open('download/out.json', 'r').readlines())
    max_hs_player=max(parser_out['players'], key=lambda x: x['hits'][1])
    hs+='Most headshots on '+parser_out['demo']['szMapName']+': '+max_hs_player['szCleanName']+' - '+str(max_hs_player['hits'][1])
    hs+=' [url='+flask_app.config['APPHOST']+'/export/'+str(match_id)+'/'+str(map_num)+']more stats...[/url]'+'\n'
    if render:
      for player in parser_out['players']:
        for spree in player['sprees']:
          web.render_new(spree[0]['dwTime']-2000,2000+spree[len(spree) - 1]['dwTime'],1,player['bClientNum'],player['szCleanName']+'s '+str(len(spree))+'-man kill',match_id,map_num)
  i=Render.query.filter(Render.gtv_match_id==match_id).count()
  comment = 'Rendered [url='+flask_app.config['APPHOST']+'/export/'+str(match_id)+']'+str(i)+ ' highlights[/url] from this match\n'
  comment += hs
  print(comment)
  if flask_app.config['APPHOST']!='http://localhost:5111':
    app.gamestv.postComment(comment, match_id)
#process_match(57709,False)

def process_league(league_id):
  matches=app.gamestv.getLeagueMatches(league_id)
  for match in matches:
    process_match(league_id,False)