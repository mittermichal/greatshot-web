import urllib.request
from html.parser import HTMLParser
import re
import json
import time
import config

#def getCookies(user,pass):
#  return


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
  
  html=opener.open(url).read().decode('iso-8859-1')
  time.sleep(1)
  print(html)
  pollId=json.loads(html)['pollID']
  print('pollid: '+str(pollId))
  params = urllib.parse.urlencode({'jsAction': 'rpcPoll','pollID': str(pollId)}).encode('UTF-8')
  url = urllib.request.Request("http://www.gamestv.org/demos/"+str(demoId), params)
  links=re.findall('\/download\/demos\/'+str(demoId)+'\/demo\d+.tv_84',json.loads(opener.open(url).read().decode('iso-8859-1'))['parm'])
  links=list(map(lambda x: 'http://www.gamestv.org'+x,links))
  return links

#print(getMatchDemosId(55944))
#print(getMatchDemosId(1322))
#downloadLinks(getDemosLinks(37408))

#getDemosLinks(1322)
