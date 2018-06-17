#!/usr/bin/python3
import os, os.path, subprocess, sys
import lib.myio as myio

browser=           'chromium'  
bittorrent_client= 'transmission-gtk'

def pkill(name):  subprocess.run(['pkill', name])

def spawn(cmd, rundir= None, env= None):
  print('spawn', str(cmd))
  if rundir:  print('spawn rundir=', rundir)
  # https://stackoverflow.com/questions/31015591/spawn-and-detach-process-in-python
  # https://stackoverflow.com/questions/2613104/why-fork-before-setsid
  spawnenv= dict(os.environ); p= None
  if env:
    for k in env.keys():  spawnenv[k]= env[k]
  try: p= subprocess.Popen(cmd, env= spawnenv, cwd= rundir, start_new_session= True)
  except Exception as e:   print('spawn EXCEPTION:', str(cmd), str(e));  return -1
  print('spawn pid', str(p.pid))
  return int(str(p.pid))
  # return value is spawned pid

def xterm_spawn(cmd, rundir= None):  return spawn(['xterm', '-e', cmd], rundir)

def launchurl(hrefurl, proxy):
  print("launchurl hrefurl ", hrefurl, "proxy=", str(proxy))

  if hrefurl.startswith('magnet:'):
    launchmagnet(hrefurl)
    return

  if hrefurl.startswith('onion:'):   proxy= 1
  if hrefurl.startswith('file:'):    proxy= 1
  if hrefurl.startswith('chrome:'):  proxy= 0

  ytvidprefix= 'https://www.youtube.com/watch?v='
  if hrefurl.startswith(ytvidprefix):
    plen= len(ytvidprefix)
    #print(hrefurl);   print(str(plen))
    ytvidcode= hrefurl[plen:];  ytvidcode= ytvidcode[:11]
    #[risk of getting no audio]cmd= 'youtube-dl -v -f worstvideo '+ ytvidcode+ '; sleep 15'
    cmd= 'youtube-dl -v '+ ytvidcode+ '; sleep 15'
    print(cmd)
    xterm_spawn(cmd, rundir= '/h/Downloads')
    return

  # "ionice chromium" trips up pkill
  # https://superuser.com/questions/478608/setting-http-proxy-for-chromium-in-shell
  proxyspec= 'http://127.0.0.1:8118';  proxyflag= '--proxy-server='+ proxyspec
  #firefoxlist= ['instapundit']
  firefoxlist= []
  # Firefox sucks, but keep options open

  flagfilespec= '/dev/shm/.torbrowser.running'
  wasproxy= os.path.isfile(flagfilespec)
  # chromium insists on everything in one session, confusing proxy with non-proxy

  for pattern in firefoxlist:
    if pattern in hrefurl:
      pkill(browser)
      os.system('nice ionice firefox-esr '+ hrefurl+ " &")
      return

  if proxy:
    print('proxy...')
    if not wasproxy:  pkill(browser)
    myio.set_proxy(proxyspec)
    subprocess.call(['touch', flagfilespec])
    spawn([browser, proxyflag, hrefurl])
  else:
    print('NO proxy...')
    if wasproxy:  pkill(browser)
    myio.clear_proxy()
    os.system('rm '+ flagfilespec)
    spawn([browser, hrefurl])

#-----------------------------------------------------------

def launchmagnet(magneturl):
  spawn([bittorrent_client, magneturl])

def launchspec(spec, proxy):
  if '://'  in spec:
    launchurl(spec, proxy)
    return
  proxy= 1
  spec= os.path.expanduser(spec)
  spawn(['pcmanfm', spec])


