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

    self.readables.append({
        'name':'x',
        'description':'Testing readable variable',
        'type':'float',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
    })
    self.writables.append({
        'name':'x',
        'description':'Testing writable variable',
        'type':'float',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
    })

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
      ['time', 'x'],
      [self.sampler.lastTime(), 1]
    ]
