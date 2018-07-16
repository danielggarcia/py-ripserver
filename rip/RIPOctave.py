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
    self.TS = 0
    self.DT = 0
    self.CD = 0
    self.CI = 0
    self.MP = 0
    self.MS = 0
    self.IrF = 0
    self.IrR = 0
    self.IrL = 0
    self.Mensaje = ""

    octave.eval('global dataArray = [];')
    octave.eval('global messageArray = {};')
    octave.eval('global TS = 0;')
    octave.eval('global DT = 0;')
    octave.eval('global CD = 0;')
    octave.eval('global CI = 0;')
    octave.eval('global MP = 0;')
    octave.eval('global MS = 0;')
    octave.eval('global IrF = 0;')
    octave.eval('global IrR = 0;')
    octave.eval('global IrL = 0;')
    octave.eval('global Mensaje = "";')
    octave.eval('global currentAction = "";')
    octave.eval('global octaveCode = "";')

    try:
      octave.addpath(self.octavePath)
      octave.robotSetup()
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

  def set(self, expid, variables, values):
    '''
    Writes one or more variables to the workspace of the current Octave session
    '''
    n = len(variables)
    #f = open('/var/log/robot/ejss.log','a')
    #f.write('[SET]: Expid(' + expid + ") Variables(" + str(variables) + ") Values(" + str(values) + ")")
    #f.close
    for i in range(n):
      try:
        octave.push(variables[i], values[i])
        octave.arduinoProcessInputs()
      except:
        pass

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
        f.close
      except:
        pass
    return toReturn

  def getValuesToNotify(self):
    lastData = octave.getLastData()
    returnValue = [
      ['time', 'TS', 'DT', 'CD', 'CI', 'MP', 'MS','IrF','IrR','IrL','Mensaje'],
      [self.sampler.lastTime(), lastData[0], lastData[1], lastData[2], lastData[3], lastData[4], lastData[5], lastData[6], lastData[7], lastData[8], 'Mensaje']
    ]
    f = open('/var/log/robot/ejss.log','a')
    f.write("[getValuesToNotify]: Variables(" + str(returnValue) + ")\n")
    f.close
    return returnValue
