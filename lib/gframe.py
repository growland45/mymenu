from tkinter import *
from lib import gw

def choosecolor(palette, name, alt= None):
  if not palette:  return alt # may be color name
  if name in palette:  return palette[name]
  if not alt:  return None
  if alt in palette:  return palette[alt]
  return alt # may be color name

class myframe(Frame):
  def __init__(self, parent, palette= None, *args, **kwargs):
    super().__init__(parent, *args, **kwargs)
    self.parent= parent;  self.root = root= parent.root;  self.palette= palette
    if palette== None:  self.palette= self.root.palette
    self.choosebg('bgcolframe')
    self.isfocusset= False;  self.scrollframe= None

  def pcolor(self, name, alt= None):
    return choosecolor(self.palette, name, alt)

  def choosebg(self, key):
    bgcolor= self.pcolor(key)
    if not bgcolor:  return
    self.bgcolor= bgcolor
    self.configure(bg= bgcolor)

  def tktarget(self):  return self   # the "parent" to feed tkinter when creating sub-widgets
  def populate(self):  return        # OVERRIDE
  def title(self, title):   self.root.title(title)

  def maybe_setfocus(self, tkw):
    if self.isfocusset:  return
    tkw.focus_set();  self.isfocusset= True

  def addwidget(self, widgetclass, pkwargs= {}, **wkwargs):
    if not 'font' in wkwargs or wkwargs['font']== None:  wkwargs['font']= gw.regularfont
    return self.addwidget_noaddfont(widgetclass, pkwargs= pkwargs, **wkwargs)

  def addwidget_noaddfont(self, widgetclass, pkwargs= {}, **wkwargs):
    tkw= widgetclass(self, **wkwargs)
    if not 'expand' in pkwargs:  pkwargs['expand']= False
    if not 'fill'   in pkwargs:  pkwargs['fill']=   X
    self.tktarget().packw(tkw, **pkwargs)
    return tkw

  def label(self, text, white= False, font= None, var= None, **wkwargs):
    return self.addwidget(gw.Wlabel, text= text, textvariable= var,
                                     font= font, white= white, **wkwargs)
  def wlabel(self, text, font= None):  return self.label(text, white= True, font=font)
  def varlabel(self, var, font= None, **wkwargs):
    return self.label(None, False, var= var, font=font, **wkwargs)

  def message(self, text, width= 700): # width is pixels, despite documentation
    fg= self.pcolor('fgedit', 'white'); bg= self.pcolor('bgedit')
    return self.addwidget(Message, text= text, width= width, fg= fg, bg= bg)

  def button(self, text, command, **wkwargs):
    return self.addwidget(Button, text= text, command= command, **wkwargs)
  def compact_button(self, text, command, **wkwargs):
    return self.addwidget(gw.Wcompactbutton, text= text, command= command, **wkwargs)
  def control_button(self, text, command):
    return self.addwidget(gw.Wcontrolbutton, text= text, command= command)
  def okbutton(self, text= 'OK', command= None):
    if command== None:  command=self.on_ok
    tkw= self.button(text, command)
    self.root.bind("<Return>", command)
    return tkw

  def checkbox(self, text, val= 0):
    return self.addwidget(gw.Wcheckbox, text= text, val= val)

  def entry(self, width=30, text=''):
    tkw= self.addwidget_noaddfont(gw.Wentry, width= width, root= self.root)
    tkw.set(text)
    self.maybe_setfocus(tkw)
    return tkw

  def packw(self, tkw, **pkwargs):  pass # override

  def subframe(self, sfclass, pkwargs= {}, **sfkwargs):
    sf= sfclass(self, **sfkwargs)
    sf.populate();   self.packw(sf, **pkwargs);
    return sf

  def subframetight(self, sfclass, pkwargs= {}, **sfkwargs):
    #print('subframetight CFG: ', str(cfg)); print('subframetight KWARGS: ', str(kwargs))
    sf= sfclass(self, **sfkwargs)
    sf.populate();   self.packw(sf, fill=NONE, expand=False, **pkwargs)
    return sf

  def update_modalparent(self):
     if not hasattr(self, 'modalparent'):  return
     modalparent= self.modalparent
     #print('update_modalparent', str(modalparent), modalparent.__class__.__name__)
     if not modalparent: return
     modalparent.refresh()

  def refresh(self):
    wlist= list(self.children.values())
    for w in wlist:  w.destroy()
    self.scrollframe= None
    self.populate()

  def vscrollsubframe(self, viewclass= None, **sfkwargs):
    # only one allowed...
    if self.scrollframe:  raise ValueError('Redundant vscrollsubframe()')

    scr= vscrollframe(self);  scr.viewclass= viewclass;  scr.sfkwargs= sfkwargs
    scr.populate();  self.packw(scr); # would rather populate before show.
    self.scrollframe= scr
    return scr.tktarget()


#--------------------------------------------------------------------

class vscrollframe(myframe):
  def populate(self):
    self.interior= None
    # https://gist.github.com/EugeneBakin/76c8f9bcec5b390e45df
    # create a canvas object and a vertical scrollbar for scrolling it
    vscrollbar = Scrollbar(self, orient= VERTICAL)
    vscrollbar.pack(fill= Y, side= RIGHT, expand= FALSE)
    canvas = Canvas(self, bd=0, highlightthickness= 0, yscrollcommand= vscrollbar.set)
    canvas.root= self
    canvas.pack(side= LEFT, fill= BOTH, expand= TRUE)
    canvas.create_rectangle(0, 0, 3000, 3000, fill= self.pcolor('bgcolframe', '#555555'))
    vscrollbar.config(command= canvas.yview)

    # reset the view
    canvas.xview_moveto(0);   canvas.yview_moveto(0)
    self.canvas= canvas

    self.pop_addinterior()

  def pop_addinterior(self, viewclass= None, sfkwargs= None):
    if not viewclass:  viewclass= self.viewclass
    else:              self.viewclass= viewclass
    if not viewclass:  return None

    if not sfkwargs:  sfkwargs= self.sfkwargs
    else:             self.sfkwargs= kwargs
    if not sfkwargs:  sfkwargs= {}

    # so can replace existing...
    if self.interior:  self.interior.destroy()

    # create a frame inside the canvas which will be scrolled with it
    canvas= self.canvas
    self.interior = interior = self.viewclass(canvas, **sfkwargs)
    interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)

    # track changes to the canvas and frame width and sync them,
    # also updating the scrollbar
    def _configure_interior(event):
      # update the scrollbars to match the size of the inner frame
      size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
      canvas.config(scrollregion="0 0 %s %s" % size)
      if interior.winfo_reqwidth() != canvas.winfo_width():
        # update the canvas's width to fit the inner frame
        canvas.config(width=interior.winfo_reqwidth())
    interior.bind('<Configure>', _configure_interior)

    def _configure_canvas(event):
      if interior.winfo_reqwidth() != canvas.winfo_width():
        # update the inner frame's width to fill the canvas
        canvas.itemconfigure(interior_id, width=canvas.winfo_width())
    canvas.bind('<Configure>', _configure_canvas)

    interior.scroller= self
    interior.populate();
    return interior

  def refresh(self):  self.pop_addinterior()

  # the "parent" to feed tkinter when creating sub-widgets
  def tktarget(self):
    if self.interior:  return self.interior
    return self


