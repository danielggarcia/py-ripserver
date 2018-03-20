'''
Created on 20/10/2015

@author: jcsombria
'''
import os.path

from jsonrpc.JsonRpcServer import JsonRpcServer
from oct2py import octave

class RIPOctave(JsonRpcServer):
  '''
  classdocs
  '''

  def __init__(self, name='RIP Octave', description='An implementation of RIP for Octave'):
    '''
    Constructor
    '''
    super().__init__(name, description)

    info = {
      'info': {
        'description': 'To get server info',
        'params': None,
        'implementation': self.info,
      },
      'connect': {
        'implementation': self.connect,
        'description': 'To start a new session',
        'params': {},
      },
      'disconnect': {
        'description': 'To finish a session',
        'implementation': self.disconnect,
      },
      'get': {
        'description': 'To read server variables',
        'params': {
          'variables': '[string]',
        },
        'implementation': self.get,
      },
      'set': {
        'description': 'To write server variables',
        'params': {
          'variables': '[string]',
          'values':'[]',
        },
        'implementation': self.set,
      },
      'eval': {
        'description': 'To evaluate arbitrary octave code',
        'params': {
          'code': '[string]',
        },
        'implementation': self.eval,
      }

    }

    for method in info:
      try:
        implementation = info[method].get('implementation')
        self.on(method, info[method], implementation)
      except:
        print('[WARNING] Ignoring invalid method')

  def connect(self):
    return True


  def disconnect(self):
    pass


  def set(self, variables, values):
    for i in range(0, len(variables)):
      name = variables[i]
      octave[name] = values


  def get(self, variables):
    toReturn = {}
    for i in range(0, len(variables)):
      name = variables[i]
      toReturn[name] = octave[name]

    return toReturn


  def eval(self, command):
    try:
      result = octave.eval(command)
    except:
      pass
    return result
