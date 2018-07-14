'''
@author: jcsombria
'''
from oct2py import octave
from rip.RIPGeneric import RIPGeneric

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
    octave.addpath(self.octavePath)
    #octave.robotSetup()

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
        'description':'Timestamp of the last sent message',
        'type':'long',
        'min':'0',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'message',
        'description':'Last readed message',
        'type':'str',
        'min':'0',
        'max':'Inf',
        'precision':'0'
      })
    self.writables.append({
        'name':'moveForward',
        'description':'Moves the robot forward, sending the signal to both engines',
        'type':'int',
        'min':'0',
        'max':'1',
        'precision':'0'
    })
    self.writables.append({
        'name':'moveBackward',
        'description':'Moves the robot backwards, sending the signal to both engines',
        'type':'int',
        'min':'0',
        'max':'1',
        'precision':'0'
    })
    self.writables.append({
        'name':'turnLeft',
        'description':'Makes the robot to turn left, sending the signal to both engines',
        'type':'int',
        'min':'0',
        'max':'1',
        'precision':'0'
    })
    self.writables.append({
        'name':'turnRight',
        'description':'Makes the robot to turn right, sending the signal to both engines',
        'type':'int',
        'min':'0',
        'max':'1',
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
    octave.addPath(self.octavePath)
    octave.endSession()

  def set(self, expid, variables, values):
    '''
    Writes one or more variables to the workspace of the current Octave session
    '''
    n = len(variables)
    for i in range(n):
      try:
        octave.push(variables[i], values[i])
      except:
        pass

  def get(self, expid, variables):
    '''
    Retrieve one or more variables from the workspace of the current Octave session
    '''
    toReturn = {}
    n = len(variables)
    for i in range(n):
      name = variables[i]
      try:
        toReturn[name] = octave.pull(name)
      except:
        pass
    return toReturn

  def getValuesToNotify(self):
    return [
      ['time', 'TS', 'DT', 'CD', 'CI', 'MP', 'MS','IrF','IrR','IrL','TSM', 'message'],
      [self.sampler.lastTime(), 13256236464576,4,252,36433,1,1,45,47,77,132536474576,'This is a test']
    ]
