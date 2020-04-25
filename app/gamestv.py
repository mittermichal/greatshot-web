import urllib.request
from html.parser import HTMLParser
import re
import json

from lxml import html

import config
from lxml import etree


def commentExists(matchId):
  opener = urllib.request.build_opener()
  opener.addheaders = [('Cookie', config.gtvcookie)]
  html=opener.open("https://www.gamestv.org/event/"+str(matchId)).read().decode('iso-8859-1')
  commentId = re.search('comment(\d+)">demotoolsbot', html)
  if (commentId!=None):
    return commentId.group(1)
  else:
    return 0

def postComment(comment,matchId):
  comment_id=commentExists(matchId)
  print(comment_id)
  if comment_id:
    editComment(comment, matchId, comment_id)
  else:
    opener = urllib.request.build_opener()
    opener.addheaders = [('Cookie', config.gtvcookie)]
    params = urllib.parse.urlencode(
      {'comm_text': comment, 'comm_replyto': 0, 'comm_id': '', 'comm_add': 'Submit'}).encode('UTF-8')
    url = urllib.request.Request("https://www.gamestv.org/event/" + str(matchId) + '/?id=' + str(matchId), params)
    a=opener.open(url).read()
  return

def editComment(comment,matchId,comm_id):
  opener = urllib.request.build_opener()
  opener.addheaders = [('Cookie', config.gtvcookie)]
  params = urllib.parse.urlencode({'comm_text': comment, 'comm_replyto': 0, 'comm_id': comm_id, 'comm_add':'Edit'}).encode('UTF-8')
  url = urllib.request.Request("https://www.gamestv.org/event/" + str(matchId)+ '/?id=' + str(matchId), params)
  opener.open(url).read()
  return

#http://www.gamestv.org/event/56437-turbot-vs-teriphendi/ => http://www.gamestv.org/demos/37488/
def getMatchDemosId(matchId):
  #return 37408
  opener = urllib.request.build_opener()
  opener.addheaders = [('Cookie', config.gtvcookie)]
  html=opener.open("https://www.gamestv.org/match/replay/"+str(matchId)).read().decode('iso-8859-1')
  demosId=re.search('<input type="radio" name="demoid" value="(\d+)', html)
  if (demosId!=None):
    return demosId.group(1)
  else:
    raise IndexError

#requests demos for match and return their links in list
def getDemosLinks(demoId):
  opener = urllib.request.build_opener()
  opener.addheaders = [('Cookie', config.gtvcookie)]
  params = urllib.parse.urlencode({'jsAction': 'rpcCall','dldemo': 'true'}).encode('UTF-8')
  url = urllib.request.Request("https://www.gamestv.org/demos/"+str(demoId), params)
  response=opener.open(url).read().decode('iso-8859-1')
  pollId=json.loads(response)['pollID']
  print(response)
  print('pollid: '+str(pollId))
  params = urllib.parse.urlencode({'jsAction': 'rpcPoll','pollID': str(pollId)}).encode('UTF-8')
  url = urllib.request.Request("https://www.gamestv.org/demos/"+str(demoId), params)
  parm = None
  while parm==None:
    response = opener.open(url).read().decode('iso-8859-1')
    j = json.loads(response)
    print(j)
    parm=j['parm']
  links=re.findall('\/download\/demos\/'+str(demoId)+'\/demo\d+.tv_84',j['parm'])
  links=list(map(lambda x: 'https://www.gamestv.org'+x,links))
  return links

def getDemosDownloadLinks(matchId):
  opener = urllib.request.build_opener()
  opener.addheaders = [('Cookie', config.gtvcookie)]
  html_s = opener.open("https://www.gamestv.org/event/" + str(matchId)).read().decode('iso-8859-1')
  root = html.fromstring(html_s)
  link = list(filter(lambda x: re.match('\/files\/\d+\-tv\-demo',x),root.xpath('//table[@class="matchDetails"]/tr/td/a/@href')))[0]
  html_s = opener.open("https://www.gamestv.org" + link).read().decode('iso-8859-1')
  root = html.fromstring(html_s)
  links = root.xpath('//table[@class="contentTable"]/tr/td[1]/a/@href')
  links = list(map(lambda x: 'https://www.gamestv.org' + x, links))
  return links


def parseMatchList(html_s, teamMatches=False):
  if teamMatches:
    content_table_start=html_s.find('<table class="contentTable">')
  else:
    content_table_start = html_s.find('<table class="contentTable" cellspacing="1">')
  content_table_end=html_s.find('</table>',content_table_start)+8
  content_table=html_s[content_table_start:content_table_end]
  root = html.fromstring(content_table)
  if teamMatches:
    return root.xpath('//tr/td[6]/a/@href')
  else:
    return root.xpath('//tr/td[7]/a/@href')

#todo: paging
def getLeagueMatches(league_id):
  opener = urllib.request.build_opener()
  opener.addheaders = [('Cookie', config.gtvcookie)]
  html = opener.open("https://www.gamestv.org/league/" + str(league_id)).read().decode('iso-8859-1')
  matchIds = list(map(lambda x: re.findall('(\d+)', x)[0],parseMatchList(html)))

  return matchIds

def getTeamMatches(team_id):
  opener = urllib.request.build_opener()
  opener.addheaders = [('Cookie', config.gtvcookie)]
  html = opener.open("https://www.gamestv.org/team/" + str(team_id)).read().decode('iso-8859-1')
  matchIds = list(map(lambda x: re.findall('(\d+)', x)[0], parseMatchList(html, True)))
  print(matchIds)
  return matchIds

def getPlayers(match_id):
  opener = urllib.request.build_opener()
  opener.addheaders = [('Cookie', config.gtvcookie)]
  html_s = opener.open("https://www.gamestv.org/event/" + str(match_id)).read().decode('iso-8859-1')
  root = html.fromstring(html_s)
  players=[]
  flags=root.xpath('//div[@class="matchlineup"]/div/img/@alt')
  names_striped = map(lambda x: x.strip(),root.xpath('//div[@class="matchlineup"]/div/text()'))
  names=list(filter(lambda x: x!='\n' and x!='' and x!='Not Announced',names_striped))
  for idx,name in enumerate(names):
    players.append({'name':name,'country':flags[idx]})
  return players

#getPlayers(17188)
#print(getMatchDemosId(55944))
#print(getMatchDemosId(1322))
#downloadLinks(getDemosLinks(37408))

#getDemosLinks(1322)
#postComment('test4',57828)

#print(getLeagueMatches(1461))

#print(getDemosDownloadLinks(618))