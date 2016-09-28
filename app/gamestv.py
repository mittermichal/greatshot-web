import urllib.request
from html.parser import HTMLParser
import re
import json
import time
import config


def commentExists(matchId):
  opener = urllib.request.build_opener()
  opener.addheaders = [('Cookie', config.gtvcookie)]
  html=opener.open("http://www.gamestv.org/event/"+str(matchId)).read().decode('iso-8859-1')
  commentId = re.search('comment(\d+)">demotoolsbot', html)
  if (commentId):
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
    url = urllib.request.Request("http://www.gamestv.org/event/" + str(matchId) + '/?id=' + str(matchId), params)
    opener.open(url).read()
  return

def editComment(comment,matchId,comm_id):
  opener = urllib.request.build_opener()
  opener.addheaders = [('Cookie', config.gtvcookie)]
  params = urllib.parse.urlencode({'comm_text': comment, 'comm_replyto': 0, 'comm_id': comm_id, 'comm_add':'Edit'}).encode('UTF-8')
  url = urllib.request.Request("http://www.gamestv.org/event/" + str(matchId)+ '/?id=' + str(matchId), params)
  opener.open(url).read()
  return

#http://www.gamestv.org/event/56437-turbot-vs-teriphendi/ => http://www.gamestv.org/demos/37488/
def getMatchDemosId(matchId):
  #return 37408
  opener = urllib.request.build_opener()
  opener.addheaders = [('Cookie', config.gtvcookie)]
  html=opener.open("http://www.gamestv.org/match/replay/"+str(matchId)).read().decode('iso-8859-1')
  demosId=re.search('<input type="radio" name="demoid" value="(\d+)', html)
  if (demosId):
    return demosId.group(1)
  else: 
    return 0

#requests demos for match and return their links in list
def getDemosLinks(demoId):
  opener = urllib.request.build_opener()
  opener.addheaders = [('Cookie', config.gtvcookie)]
  params = urllib.parse.urlencode({'jsAction': 'rpcCall','dldemo': 'true'}).encode('UTF-8')
  url = urllib.request.Request("http://www.gamestv.org/demos/"+str(demoId), params)

  response=opener.open(url).read().decode('iso-8859-1')
  print(response)
  pollId=json.loads(response)['pollID']
  print('pollid: '+str(pollId))
  params = urllib.parse.urlencode({'jsAction': 'rpcPoll','pollID': str(pollId)}).encode('UTF-8')
  url = urllib.request.Request("http://www.gamestv.org/demos/"+str(demoId), params)
  parm = None
  while parm==None:
    response = opener.open(url).read().decode('iso-8859-1')
    j = json.loads(response)
    print(j)
    parm=j['parm']
  links=re.findall('\/download\/demos\/'+str(demoId)+'\/demo\d+.tv_84',j['parm'])
  links=list(map(lambda x: 'http://www.gamestv.org'+x,links))
  return links

#print(getMatchDemosId(55944))
#print(getMatchDemosId(1322))
#downloadLinks(getDemosLinks(37408))

#getDemosLinks(1322)
#postComment('test4',57100)
