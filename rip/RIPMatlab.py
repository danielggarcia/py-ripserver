'''
@author: jcsombria
'''
import os.path

from rip.RIPGeneric import RIPGeneric
from .MatlabConnector import CommandBuilder, MatlabConnector
from .SimulinkConnector import SimulinkConnector

import matlab.engine

class RIPMatlab(RIPGeneric):
  '''
  RIP MATLAB Adapter
  '''

  def __init__(self, name='Octave', description='An implementation of RIP to control Octave', authors='J. Chacon', keywords='Octave'):
    '''
    Constructor
    '''
    super().__init__(name, description, authors, keywords)

    self.commandBuilder = CommandBuilder()
    self.matlab = MatlabConnector()
    self.simulink = SimulinkConnector()

    self.addMethods({
      'connect': { 'description': 'Start a new MATLAB session',
        'params': {},
        'implementation': self.connect,
      },
      'disconnect': { 'description': 'Finish the current MATLAB session',
        'params': {},
        'implementation': self.disconnect,
      },
      'get': { 'description': 'Read variables from the MATLAB\'s workspace',
        'params': { 'expId': 'string', 'variables': '[string]' },
        'implementation': self.get,
      },
      'set': { 'description': 'Send values to variables in the MATLAB\'s workspace',
        'params': { 'expId': 'string', 'variables': '[string]', 'values':'[]' },
        'implementation': self.set,
      },
      'eval': { 'description': 'Run MATLAB code',
        'params': { 'expId': 'string', 'code': '[string]'},
        'implementation': self.set,
      },
    })

  def connect(self):
    self._matlab = matlab.engine.start_matlab('-desktop')
    self.simulink.set
    return True

  def disconnect(self):
    self._matlab.quit()

  def set(self, variables, values):
    self.matlab.set(variables, values)

  def get(self, variables):
    return self.matlab.get(variables)

  def eval(self, command):
    try:
      result = self._matlab.eval(command, nargout=0)
    except:
      pass
    return result

  # def _open(self, path):
  #   try:
  #     #open
  #     dirname = os.path.dirname(path)
  #     cd = self.commandBuilder.cd(dirname)
  #     model = os.path.basename(path)
  #     load_system = self.commandBuilder.load_system(model)
  #     command = cd + load_system
  #     result = self._matlab.eval(command, nargout=0)
  #     #addEjsSubsystem
  #     _load_model(model)
  #
  #   except:
  #     return None
  #   return result
  #
  # def _load_model(self, model):
  #   command = self.commandBuilder.addEjsSubblock(model) + \
  #     self.commandBuilder.addPauseBlock(model) + \
  #     self.commandBuilder.set_param(model, "StartTime", "0") + \
  #     self.commandBuilder.set_param(model, "StopTime", "inf")
  #   self._matlab.eval(command)
  #
  #
  # def _step(self, command):
  #   try:
  #     result = self._matlab.eval(command, nargout=0)
  #   except:
  #     return None
  #   return result
