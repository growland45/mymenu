from tkinter import Button, Checkbutton, END, Entry, IntVar
from tkinter import Label, OptionMenu, Scrollbar, StringVar, Text

entryfont= ('Courier New', 12)
tinyfont= ('TkTextFont', 10)
controlbuttonfont= ('TkTextFont', 11)
regularfont= ('TkTextFont', 12)

def safeget(dict, key):
  if not dict:  return None
  if key in dict:  return dict[key]
  return None

def defaultset(kwargs, key, val= None):
  if key in kwargs:  return
  kwargs[key]= val

#--------------------------------------------------------------------
class Wcompactbutton(Button):
  def __init__(self, parent, *args, **kwargs):
    super().__init__(parent, *args, **kwargs)
    self.config(padx= 1, pady= 1)

class Wcontrolbutton(Button):
  def __init__(self, parent, *args, **kwargs):
    super().__init__(parent, *args, **kwargs)
    color= parent.pcolor('control_button');  self.config(background= color)
    self.config(font= controlbuttonfont)
    self.config(padx= 1, pady= 1, relief= 'flat')

#--------------------------------------------------------------------
class Wcheckbox(Checkbutton):
  def __init__(self, parent, val= 0, *args, **kwargs):
    self.default= val
    iv= IntVar();  iv.set(val)
    super().__init__(parent, variable= iv, *args, **kwargs)
    self.iv= iv

  def get(self):
    try:               val= self.iv.get()
    except Exception:  return self.default
    return val

  def set(self, val):  self.iv.set(str(val))

#--------------------------------------------------------------------
class Wlabel(Label):
  def __init__(self, parent, white= False, *args, **kwargs):
    #print('Wlabel kwargs:', str(kwargs))
    super().__init__(parent, *args, **kwargs)
    if hasattr(parent, 'bgcolor'):  self.config(bg= parent.bgcolor)
    dflt= 'black'
    if white:  dflt= 'white'
    self.config(fg= parent.pcolor('textcolor', dflt))

#--------------------------------------------------------------------
class Wentry(Entry):
  def __init__(self, parent, root, *args, **kwargs):
    global entryfont; palette= self.palette= parent.palette
    defaultset(kwargs, 'font',             entryfont)
    defaultset(kwargs, 'bg',               safeget(palette, 'bgedit'))
    defaultset(kwargs, 'fg',               safeget(palette, 'fgedit'))
    defaultset(kwargs, 'insertbackground', safeget(palette, 'fgedit'))
    super().__init__(parent, *args, **kwargs)
    self.config(font= entryfont)
    self.bind("<Control-KeyRelease-a>", Wentry.entry_on_ctl_a)

  def entry_on_ctl_a(event):
    # https://stackoverflow.com/questions/41477428/ctrl-a-select-all-in-entry-widget-tkinter-python
    event.widget.select_range(0, 'end')

  #def get(self):  return super().get().rstrip()) # TK bug?
  def set(self, text):  self.delete(0, 'end');   self.insert(0, text)

#--------------------------------------------------------------------
class Woptionmenu(OptionMenu):
  # http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/optionmenu.html
  def __init__(self, parent, optionlist, val= ''):
    sv= StringVar();  sv.set(str(val))
    self.optionlist= optionlist
    super().__init__(parent, sv, *self.optionlist)
    self.sv= sv

  def get(self):       s= self.sv.get();  return str(s)
  def getint(self):    s= self.sv.get();  return int(s)
  def set(self, val):  self.sv.set(str(val))

#--------------------------------------------------------------------
def pop_messagesection(parent, title= '', text= '', clipput= None):
  gf= parent.gridf(1)
  cr= gf.ctlrow()
  cr.wlabel(title)
  if clipput:
    cr.control_button(text= 'Clip', command= lambda text= text: clipput(text))
  gf.message(text)

#--------------------------------------------------------------------
# https://stackoverflow.com/questions/13832720/how-to-attach-a-scrollbar-to-a-text-widget

def pop_textpane(parent, height= 25, width= 60): # parent should be g.rowframe
  global entryfont
  bgcolor= parent.pcolor('bgedit');  fgcolor= parent.pcolor('fgedit')
  parent.txt= parent.addwidget_noaddfont(Text,
                                         borderwidth=      3,
                                         relief=           'sunken',
                                         undo=             True,
                                         wrap=             'word',
                                         background=       bgcolor,
                                         foreground=       fgcolor,
                                         insertbackground= fgcolor,
                                         height=           height,
                                         width=            width,
                                         font=             entryfont)
  parent.scrollb= parent.addwidget_noaddfont(Scrollbar,
                                             pkwargs={'fill': 'both', 'sticky': 'nsew'},
                                             command= parent.txt.yview)
  # The part that will address your Scrollbar being small is sticky='nsew',
  parent.txt['yscrollcommand'] = parent.scrollb.set
  parent.txt.bind("<Control-KeyRelease-a>", tp_on_ctl_a)

def tp_on_ctl_a(event):   event.widget.tag_add("sel",'1.0','end')

def get_textpane(parent):        return parent.txt.get('1.0', END)
def set_textpane(parent, text):  parent.txt.delete('1.0', END);  parent.txt.insert(END, text)
def append_textpane(parent, text):  parent.txt.insert(END, text);  parent.txt.see(END)


#------------------------------------------------------------------------------------

class widgets2dict:
  def __init__(self, dict, notouch= None):
    assert dict;  self.dict= dict;  self.notouch= notouch;  self.assocs= []

  def assoc(self, tkw, key):
    assert tkw;  assert key;  notouch= self.notouch
    if notouch and key in notouch:  return None
    self.assocs.append((tkw, key));  return tkw

  def dict2widgets(self, dict= None):
    if not dict:  dict= self.dict;  assert dict
    for tuple in self.assocs:
      tkw= tuple[0];  key= tuple[1];  assert tkw;  assert key
      if key in dict:
        val= dict[key]
        if not val:  val= ''
        tkw.set(str(val))

  def widgets2dict(self, dict= None):
    if not dict:  dict= self.dict;  assert dict
    for tuple in self.assocs:
      tkw= tuple[0];  key= tuple[1];  assert tkw;  assert key
      dict[key]= str(tkw.get())

  def add_labelblanks(self, parent):
    notouch= self.notouch
    sg= parent.gridf(2);
    for key in sorted(self.dict.keys()):
      if notouch and key in notouch:  continue
      sg.wlabel(key);  wentry= sg.entry(width=60);  self.assoc(wentry, key)
    self.dict2widgets()


