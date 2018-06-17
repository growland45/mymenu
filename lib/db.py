import sqlite3

def sqlite_open(dbspec):
  conn= sqlite3.connect(dbspec)
  conn.row_factory = sqlite3.Row
  return conn

def safedict_string(rdict, key, default= ''):
  if not key in rdict:  return default
  val= str(rdict[key])
  if val!= 'None':  return val
  return ''

def safedict_int(rdict, key, default= 0):
  if not key in rdict:  return default
  val= rdict[key]
  if val and (val!= 'None'):  return int(val)
  return default

class Rec:
  def __init__(self, nt= None):
    self.dict= {}
    if nt:  self.load(nt)

  def load(self, nt):
    for k in nt.keys():  self.dict[str(k)]= str(nt[k])

  def print(self):
    for k in self.dict.keys():  print(k+ ": "+ self.dict[k])

  def button_text(self, maxwid= 90):
    dict= self.dict;  btext= None
    if 'title' in dict:   btext= dict['title']
    if not btext and 'name' in dict:   btext= dict['name']
    if not btext and 'spec' in dict:   btext= dict['spec']
    if btext!= '' and btext!= 'None':  return btext[:maxwid]
    #print('NO title OR spec')
    return None

#----------------------------------------------------------------

class dbrec(Rec):
  def __init__(self, table, nt= None):
    self.table= table;  safent= {}
    for k in nt.keys():
      val= nt[k]
      if not val:  val= ''
      safent[k]= val
    super().__init__(safent)

  def safeint(self, key, *args):  return safedict_int(   self.dict, key, *args)
  def safestr(self, key, *args):  return safedict_string(self.dict, key, *args)

  def delete(self):
    table= self.table;  keyfield= table.keyfield;  key= self.dict[keyfield]
    print('dbrec.delete:', key)
    table.delete(key)

  def save(self):
    rdict= self.dict; table= self.table
    #print('dbrec.save', table.tname, str(dict))
    table.save(rdict)

#------------------------------------------------------------------------------

class dbtable:
  def __init__(self, conn, tname, orderby= None, recclass= dbrec, keyfield= None):
    self.conn= conn;  self.tname= tname;
    self.orderby= orderby;  self.recclass= recclass
    self.keyfield= keyfield

  def create(self, schema):
    sql= 'CREATE TABLE if not exists '+ self.tname+ ' ('+ schema+ ')'
    # remember PRIMARY KEY(key1,key2) as needed
    self._sql_exec(sql, commit= True)

  def create_index(self, fields):
    iname= 'i'+ fields.join('')
    sfields= fields.join(',')
    sql= "CREATE INDEX IF NOT EXISTS "+ iname+ ' ON '+ self.tname+ ' ('+ sfields+ ')'
    self._sql_exec(sql, commit= True)

  def delete(self, keyval):
    sql= 'DELETE FROM '+ self.tname+ ' WHERE '+ self.keyfield+ '=?';
    self._sql_exec(sql, [keyval], commit= True)

  def select(self, fields='*', where= None, orderby= None,
                   limit= None, listener= None, vals= None):
    if (not orderby) and self.orderby:  orderby= self.orderby
    sql= 'SELECT '+ fields+ ' FROM '+ self.tname
    if where:   sql= sql+ ' WHERE '+ where
    if orderby: sql= sql+ ' ORDER BY '+ orderby
    if limit:   sql= sql+ ' LIMIT '+ str(limit)
    #self.conn.row_factory = sqlite3.Row
    #print(sql, str(vals))
    c= self._sql_exec(sql, vals)
    #self.conn.row_factory = None
    if not listener:  return c

    for nt in c:
      rec= self.recclass(self, nt)
      listener.handle_dbrec(rec)

  def has(self, keyval):
    c= self.select(where= self.keyfield+ '=?', vals= [keyval])
    if not c:  return False
    nt= c.fetchone()
    if not nt:  return False
    return True

  def fetchone(self, c, target= None):
    #print('fetchone', str(self), str(c))
    if not c:  return None
    nt= c.fetchone()
    if not nt:  return None
    return self._read_postfetch(nt, target)

  def read(self, keyval, target= None):
    c= self.select(where= self.keyfield+ '=?', vals= [keyval])
    nt= c.fetchone()
    if not nt:  return None
    return self._read_postfetch(nt, target)

  def readrandom(self, where= None):
    c= self.select(where= where, orderby= 'RANDOM()', limit= 1)
    nt= c.fetchone()
    if not nt:  return None
    return self._read_postfetch(nt)

  def _read_postfetch(self, nt, target= None):
    #print('_read_postfetch, recclass=', str(self.recclass))
    if not target:  return self.recclass(self, nt)
    # useful for revert...
    target.load(nt);   return target

  def save(self, rdict, readback= False):  self.replace_into(rdict, readback)

  def update_set(self, sdict, keyval= None, where= None, wherevals= None):
    setsql= '';  setsql= '';  vals= []; first= True
    keyfield= self.keyfield
    for fname in sdict.keys():
      if fname== keyfield:  continue
      if not first:  setsql= setsql+ ','
      first= False;  setsql= setsql+ fname+ '=?'
      vals.append(sdict[fname])
    if keyval:       vals.append(keyval)
    elif keyfield:   vals.append(sdict[keyfield])
    if not where:    assert(keyfield);  where= keyfield+ '=?'
    elif wherevals:  vals.extend(wherevals)
    sql= 'UPDATE '+ self.tname+ ' SET '+ setsql+ ' WHERE '+ where;
    print(sql);  print(vals)
    self._sql_exec(sql, vals, commit= True)

  def replace_into(self, rdict, readback= False):
    namesql= '';  varsql= '';  vals= []; first= True
    for fname in rdict.keys():
      if not first:  namesql= namesql+ ',';    varsql= varsql+ ','
      first= False;  namesql= namesql+ fname;  varsql= varsql+ '?'
      vals.append(rdict[fname])
    sql= 'REPLACE INTO '+ self.tname+ ' ('+ namesql+ ') VALUES ('+ varsql+ ')';
    #print(sql); print(vals)
    self._sql_exec(sql, vals, commit= True)
    if not readback:  return

    # for use with id autoincrement
    c= self.select(orderby= 'id desc', limit= 1);  nt= c.fetchone()
    for k in nt.keys():  rdict[str(k)]= str(nt[k])

  def _sql_exec(self, sql, vals= None, commit= False):
    c= self.conn.cursor()
    try:
      if vals:  c.execute(sql, vals)
      else:     c.execute(sql)
    except Exception as e:
      print('BAD SQL: ', sql, 'VALS:', str(vals));  print(str(e))
    if commit:  self.conn.commit()
    return c
