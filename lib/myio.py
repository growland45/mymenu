import urllib.request, urllib.parse
import http.client
import os, re, socket, subprocess, sys
from html.parser import HTMLParser

def dbg(text):  print (text, file= sys.stderr)

def set_proxy(proxystring):
  os.environ['http_proxy']=  proxystring
  os.environ['https_proxy']= proxystring

def clear_proxy():
  if 'http_proxy'  in os.environ:  del os.environ['http_proxy'];
  if 'https_proxy' in os.environ:  del os.environ['https_proxy'];
  os.unsetenv('http_proxy')
  os.unsetenv('https_proxy')
  # https://stackoverflow.com/questions/3575165/what-is-the-correct-way-to-unset-a-linux-environment-variable-in-python

def attend_to_http_proxy():
  if 'http_proxy' in os.environ:
    http_proxy= os.environ['http_proxy']
    if http_proxy== '':  return
    proxies = {'http':  http_proxy, 'https': http_proxy}
    proxy_support = urllib.request.ProxyHandler(proxies)
    opener = urllib.request.build_opener(proxy_support)
    #urllib.request.install_opener(opener)
    sys.stderr.write("myio proxy: '"+ http_proxy+ "'\n")
    return opener
  return None

def html_decrappify(html):
  html = html.replace('\n', ' ').replace('\r', '').strip()
  # TODO?
  return html

def fetchurl(url, postdict= None):
  decoded= None
  # fetch the url and parse it through htmlparser
  # postdict is optional dictionary of post data
  i= url.find('#')
  if i> 0:  url= url[:i]
  opener= attend_to_http_proxy()

  postdata= None
  if (postdict):
    print('postdict', str(postdict))
    postdata = urllib.parse.urlencode(postdict).encode()

  try:
    req = urllib.request.Request(url, data= postdata, 
       headers= { 'User-Agent':
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) '+
                    'AppleWebKit/537.36 (KHTML, like Gecko) '+
                    'Chrome/35.0.1916.47 Safari/537.36'
       } )
    if opener== None:  r1= urllib.request.urlopen(req, timeout=20)
    else:              r1= opener.open(req, timeout=20)
  except Exception as e:  return ("FAILED "+ url+ " EXCEPTION "+ str(e), None)

  if r1.status!= 200:  return ("STATUS "+ str(r1.status)+ ' '+ r1.reason, None)

  data1 = r1.read(); # bytes object
  decoded= data1.decode("utf-8", errors='ignore')
  return ("STATUS "+ str(r1.status)+ ' '+ r1.reason, decoded)

#---------------------------------------------------------------------

class html_fetcher_parser(HTMLParser):
  decoded= None

  def __init__(self, html= None, url= None, postdict= None, proxyspec= None):
    super().__init__()
    self.html= html
    if html:   self.feed(html)
    elif url:  self.dofetch(url, postdict= postdict, proxyspec= proxyspec)

  def dofetch(self, url, postdict= None, proxyspec= None):
    if proxyspec:  set_proxy(proxyspec)
    tuple= fetchurl(url, postdict= postdict)
    if proxyspec:  clear_proxy()
    self.status= tuple[0];  self.html= tuple[1]

  def dourl(self, url, postdict= None, proxyspec= None):
    self.dofetch(url, postdict= postdict, proxyspec= proxyspec)
    if self.html:  self.feed(self.html)
    print('myio.dourl status=', self.status)
    return self.status

  def doit(self):
    if self.html:  self.feed(self.html)
    print('myio.dourl status=', self.status)
    return self.status

#------------------------------------------------------------------------------

class html_extract_parser(html_fetcher_parser):
  title= ''; intitle= False
  hrefurl= ''; inhref= False

  def handle_starttag(self, tag, attrs):
    if tag=='title':  return self.handle_starttitletag(tag, attrs)
    if tag=='a':      return self.handle_startatag(tag, attrs)

  def handle_data(self, data):
    if self.inhref:   self.hreftitle= self.hreftitle+ ' '+ html_decrappify(data)
    if self.intitle:  self.title=     self.title+          html_decrappify(data)

  def handle_endtag(self, tag):
    if self.inhref:   self.handle_href()
    if self.intitle:  self.handle_title()

  def handle_starttitletag(self, tag, attrs):
    self.intitle= True;

  def handle_startatag(self, tag, attrs):
    self.hreftitle= ''
    for attr in attrs:
      ttype= attr[0];  val= attr[1]
      if ttype=='href':
        self.inhref= True; self.hrefurl= val

  def handle_href(self):
    self.inhref= False;
    hrefurl= self.hrefurl; hreftitle= self.hreftitle
    hrefurl=   html_decrappify(hrefurl)
    hreftitle= html_decrappify(hreftitle)
    if not self.decide_accept_href(hrefurl, hreftitle):  return

    self.hrefurl= '';  self.hreftitle= ''
    self.emit_href(hrefurl, hreftitle)

  def handle_title(self):
    self.emit_title();   self.intitle= False

  # callbacks to override...
  def decide_accept_href(self, hrefurl, hreftitle):  return True
  def emit_href(self, hrefurl, hreftitle): pass
  def emit_title(self):                    pass

#---------------------------------------------------------------------

def global_ip():  p= MyIPParser();  p.doit();  return p.ip
def proxy_ip(proxy):  p= MyIPParser();  p.doit(proxy= proxy);  return p.ip
def tor_restart():  subprocess.run(['gksu', '/etc/init.d/tor', 'restart'])

class MyIPParser(html_fetcher_parser):
  ip= None

  def doit(self, proxy= None):
    #url= 'http://www.whatsmyip.org/'
    url= 'https://www.iplocation.net/find-ip-address'
    # https://www.ipaddress.com/
    return self.dourl(url, proxyspec= proxy)

  def handle_data(self, data):
    if self.ip!= None:  return
    text= str(data)
    result = re.findall(r'[0-9]+(?:\.[0-9]+){3}', text)
    if len(result)< 1:  return
    self.ip= result[0]
    print(text)

#---------------------------------------------------------------------
class DuckResultParser(html_fetcher_parser):
  hrefurl= ''; inhref= False;  prevurl= '';  count= 0;

  def __init__(self, max=500, keywords= None):
    HTMLParser.__init__(self)
    self.max= max;  self.keyords= keywords
    if keywords:  self.dofetch_keywords(keywords)

  def dofetch_keywords(self, keywords, proxy= None):
    url= 'https://duckduckgo.com/html'
    dd= {};  dd['q']= keywords;
    self.dofetch(url, postdict= dd, proxy= proxy)

  def doit(self, keywords= None):
    if keywords:  self.keywords= keywords;  self.dofetch_keywords(keywords)
    if self.html:  self.feed(self.html)
    return self.status

  def handle_starttag(self, tag, attrs):
    if tag=='a':  return self.handle_startatag(tag, attrs)

  def handle_startatag(self, tag, attrs):
    self.hreftitle= ''
    for attr in attrs:
      ttype= attr[0];  val= attr[1]
      if ttype=='href':
        self.inhref= True; self.hrefurl= val

  def handle_data(self, data):
    if self.inhref:
      self.hreftitle= self.hreftitle+ ' '+ DuckResultParser.html_decrappify(data)

  def handle_endtag(self, tag):
    if self.inhref:  self.handle_href()
    self.inhref= False;

  def handle_href(self):
    hrefurl= self.hrefurl
    if hrefurl== self.prevurl:  return
    if (hrefurl.startswith('http') and not ('duckduckgo.com' in hrefurl)):
      self.handle_search_result(hrefurl, self.hreftitle)
    self.hrefurl= '';  self.hreftitle= ''
    self.prevurl= hrefurl

  def html_decrappify(html):
    html = html.replace('\n', ' ').replace('\r', '')
    return html

 
