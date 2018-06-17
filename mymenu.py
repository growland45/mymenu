#!/usr/bin/python3
# replacememt for launch.pl
import glob, os, subprocess
from lib import db, g, gw, mylaunch

ourdbspec= 'launchables.sqlite'
titleprefix= 'LM '
ourconn= ourconn= db.sqlite_open(ourdbspec)
tl=  db.dbtable(ourconn, 'launchable',  keyfield= 'command', orderby= 'name')
ts=  db.dbtable(ourconn, 'sysfiles',    keyfield= 'file',    orderby= 'file')


palette= { 'bggrid': '#111177', 'bgedit': '#000044', 'fgedit': 'white',
           'bgcolframe': '#000066',
           'control_button': '#5555aa', 'doc_button': '#ccccdd'}

class Fwhichever(g.packframe):
  def __init__(self, parent, isroot, *args, **kwargs):
    super().__init__(parent, *args, **kwargs)
    self.isroot= isroot

  def populate(self):
    ourfont= ('TkTextFont', 11)
    doccolor= self.pcolor('doc_button', 'gray')
    rf= self.rowf()
    lc= rf.colf(); 
    if self.isroot: lc.wlabel('Root commands:')
    g= lc.gridf(2)
    c= tl.select()
    for nt in c:
      if not self.isourroot(nt):  continue
      name= nt['name'];  cmd= lambda nt=nt: self.launch_command(nt)
      g.button(text= name, command= cmd, font=ourfont)
    rc= rf.colf()
    rc.wlabel('Config files:');  cfc= rc.gridf(2)
    rc.wlabel('Log files:');     lfc= rc.gridf(2)
    c= ts.select()
    for nt in c:
      if not self.isourroot(nt):  continue
      file= nt['file'];  type= nt['type']
      if type== 'log'  or type== 'view':
        cmd= lambda nt=nt: self.launch_logfile(nt)
        lfc.compact_button(text= file[-32:], command=cmd, background=doccolor, font=ourfont)
      else:
        cmd= lambda nt=nt: self.launch_configfile(nt)
        cfc.compact_button(text= file[-32:], command=cmd, background=doccolor, font=ourfont)

  def isroottask(self, nt):
    root= str(nt['root']);  isroot= self.isroot
    if root== 'None' or root=='':  root= '0'
    return root

  def isourroot(self, nt):
    isroot= self.isroot;  root= self.isroottask(nt)
    #print('root', root, 'self.isroot', str(isroot))
    if isroot and (root== '0'):       return False
    if not(isroot) and (root== '1'):  return False
    return True

  def launch_command(self, nt):
    command= nt['command'];  cwd= nt['cwd'];  gui= str(nt['gui'])
    cmd= cs= command.split()
    if self.isroot:  cmd= ['gksu'];  cmd.extend(cs)
    if cwd== '':  cwd= None
    if gui== '1':   mylaunch.spawn(cmd= cmd, rundir= cwd)
    else:           mylaunch.xterm_spawn(cmd= cmd, rundir= cwd)

  def launch_configfile(self, nt):
    filespec= os.path.expanduser(nt['file']); #print(file)
    viewer= 'pluma'
    if filespec.endswith('sqlite'):  viewer= 'sqlitebrowser'
    if self.isroot:  cmd= ['gksu', viewer]
    else:            cmd= [viewer]
    filelist= glob.glob(filespec)    #print(filelist)
    cmd.extend(filelist);    mylaunch.spawn(cmd)

  def launch_logfile(self, nt):
    self.launch_configfile(nt)

#=================================================================================

class Fuser(Fwhichever):
  def __init__(self, parent, *args, **kwargs):
    super().__init__(parent, isroot= False, *args, **kwargs)

class Froot(Fwhichever):
  def __init__(self, parent, *args, **kwargs):
    super().__init__(parent, isroot= True, *args, **kwargs)

class Fmain(g.packframe):
  class Fscrolled(g.packframe):
    def populate(self):
      self.title('LAUNCH MENU')
      self.subframe(Fuser)
      self.subframe(Froot)
      self.control_button('Database', command= self.g_dbedit)
    def g_dbedit(self):
      subprocess.call(['sqlitebrowser', ourdbspec])
      self.refresh()
  def populate(self):  self.vscrollsubframe(Fmain.Fscrolled)

if __name__ == '__main__':
  g.justone('mymenu')
  g.domain(Fmain, palette= palette, fullscreen= True)

 
