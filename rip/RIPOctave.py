'''
@author: jcsombria
'''
from oct2py import octave
from rip.RIPGeneric import RIPGeneric
from random import random
import numpy as np

class RIPOctave(RIPGeneric):
  '''
  RIP Octave Adapter
  '''
  def __init__(self, name='Octave', description='An implementation of RIP to control Octave', authors='J. Chacon', keywords='Octave'):
    '''
    Constructor
    '''
    super().__init__(name, description, authors, keywords)
    self.octavePath = '/home/pi/workspace/robot/octave'
    self.dataArray = []
    self.messageArray = {}
    self.TS = 0.0
    self.DT = 0.0
    self.CD = 0.0
    self.CI = 0.0
    self.MP = 0.0
    self.MS = 0.0
    self.IrF = 0.0
    self.IrR = 0.0
    self.IrL = 0.0
    self.previousMessage = []
    
    octave.eval('global dataArray;')
    octave.eval('global messageArray;')
    octave.eval('global TS;')
    octave.eval('global DT;')
    octave.eval('global CD;')
    octave.eval('global CI;')
    octave.eval('global MP;')
    octave.eval('global MS;')
    octave.eval('global IrF;')
    octave.eval('global IrR;')
    octave.eval('global IrL;')

    #octave.eval('global currentAction;')
    octave.eval('global octaveCode;')
    octave.eval('global debugLevel;')
    
    try:
      self.initSession()
    except:
      pass

    self.readables.append({
        'name':'TS',
        'description':'Timestamp of the reading',
        'type':'long',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'DT',
        'description':'Time from the previous lecture',
        'type':'long',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'CD',
        'description':'Number of counts from right decoder',
        'type':'int',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'CI',
        'description':'Number of counts from left decoder',
        'type':'int',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'MP',
        'description':'Engine status (0=off, 1=on)',
        'type':'int',
        'min':'0',
        'max':'1',
        'precision':'0'
      })
    self.readables.append({
        'name':'MS',
        'description':'Laser status (0=off, 1=on)',
        'type':'int',
        'min':'0',
        'max':'1',
        'precision':'0'
      })
    self.readables.append({
        'name':'IrF',
        'description':'Distance (in cm) readed by frontal sensor',
        'type':'int',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'IrR',
        'description':'Distance (in cm) readed by right sensor',
        'type':'int',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'IrL',
        'description':'Distance (in cm) readed by left sensor',
        'type':'int',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'TSM',
        'description':'Timestamp of the message reading',
        'type':'long',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'Mensaje',
        'description':'Last readed message',
        'type':'str',
        'min':'0',
        'max':'Inf',
        'precision':'0'
      })
    self.writables.append({
        'name':'currentAction',
        'description':'Sets an action to perform in the robot: D(-255,255), I(-255,255),P,K,F,B,L,R,S,U',
        'type':'str',
        'min':'0',
        'max':'Inf',
        'precision':'0'
    })
    self.writables.append({
        'name':'octaveCode',
        'description':'Sets a string with octave code to be executed in the server',
        'type':'str',
        'min':'0',
        'max':'Inf',
        'precision':'0'
    })

  def __del__(self):
    octave.endSession()

  # This method will be invoked from HttpServer.SSE
  def start(self):
    octave.addpath(self.octavePath)
    octave.robotSetup()
    octave.arduinoProcessInputs("K")

  def set(self, expid, variables, values):
    '''
    Writes one or more variables to the workspace of the current Octave session
    '''
    n = len(variables)
    f = open('/var/log/robot/ejss.log','a')
    f.write('[SET]: Expid(' + expid + ") Variables(" + str(variables) + ") Values(" + str(values) + ")")
    
    for i in range(n):
      try:
        f.write('[SET]: Variable: ' + str(variables[i] + "; value: " + str(values[i])))
        if(variables[i] == 'currentAction'):
          octave.arduinoProcessInputs(values[i])
        elif(variables[i] == 'octaveCode'):
          octave.executeOctaveCode(values[i])
      except Exception as e:
        f.write("Error al realizar el SET: " + str(e))
        pass
    f.close
  def get(self, expid, variables):
    '''
    Retrieve one or more variables from the workspace of the current Octave session
    '''
    toReturn = {}
    f = open('/var/log/robot/ejss.log','a')
    f.write("[GET]: Expid(" + expid + ") ENTERING)\n")
    n = len(variables)
    for i in range(n):
      name = variables[i]
      try:
        toReturn[name] = octave.pull(name)
        f.write('[GET]: Expid(' + expid + ") Variables(" + str(variables) + ") toReturn(" + str(toReturn) + ")\n")
        f.close()
      except:
        pass
    return toReturn

  def getValuesToNotify(self):
    f = open('/var/log/robot/ejss.log','a')
    returnValue = self.previousMessage
    try:
      self.TS = 0
      self.DT = 0
      self.CD = 0
      self.CI = 0
      self.MP = 0
      self.MS = 0
      self.IrF = 0
      self.IrR = 0
      self.IrL = 0
      result = octave.updateGlobals()
      f.write("Result: " + str(type(result)) + ", " + str(result) + "\n")
      if type(result) is list:
        pass
      elif type(result) is np.ndarray and result.size == 9:
        if type(result.item(0)) is float:
          self.TS = result.item(0)
        if type(result.item(1)) is float:
          self.DT = result.item(1)
        if type(result.item(2)) is float:
          self.CD = result.item(2)
        if type(result.item(3)) is float:
          self.CI = result.item(3)
        if type(result.item(4)) is float:
          self.MP = result.item(4)
        if type(result.item(5)) is float:
          self.MS = result.item(5)
        if type(result.item(6)) is float:
          self.IrF = result.item(6)
        if type(result.item(7)) is float:
          self.IrR = result.item(7)
        if type(result.item(8)) is float:
          self.IrL = result.item(8)
      try:
        msg = octave.getLastMessage()
        if msg.size == 2:
          self.TSM = int(msg.item(0))
          self.Mensaje = msg.item(1)
      except Exception as e:
        f.write("Error retrieving messages from server: " + str(e))
        self.TSM = 0
        self.Mensaje = ""
        pass
      returnValue = [
        ['time', 'TS', 'DT', 'CD', 'CI', 'MP', 'MS','IrF','IrR','IrL', 'TSM', 'Mensaje'],
        [self.sampler.lastTime(), self.TS, self.DT, self.CD, self.CI, self.MP, self.MS, self.IrF, self.IrR, self.IrL, self.TSM, self.Mensaje]
      ]
      self.previousMessage = returnValue
      f.close()
    except Exception as e:
      returnValue = [['id', 'Mensaje'], [-1, str(e)]]
      f.close()
    return returnValue
