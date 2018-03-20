'''
Created on 20/10/2015

@author: jcsombria
'''
import os.path

from jsonrpc.JsonRpcServer import JsonRpcServer
from app.MatlabConnector import CommandBuilder, MatlabConnector
from app.SimulinkConnector import SimulinkConnector

import matlab.engine

class RIPMatlab(JsonRpcServer):
  '''
  classdocs
  '''

  def __init__(self):
    '''
    Constructor
    '''
    super().__init__()
    self.on('connect', 0, self._connect)
    self.on('disconnect', 0, self._disconnect)
    self.on('get', 1, self._get)
    self.on('set', 2, self._set)
    self.on('eval', 1, self._eval)
    self.on('open', 1, self._open)
    self.on('step', 1, self._step)
    self.commandBuilder = CommandBuilder()
    self.matlab = MatlabConnector()
    self.simulink = SimulinkConnector()
  
  def _connect(self):
    self._matlab = matlab.engine.start_matlab('-desktop')
    self.simulink.set
    return True


  def _disconnect(self):
    self._matlab.quit()


  def _set(self, variables, values):
    self.matlab.set(variables, values)


  def _get(self, variables):
    return self.matlab.get(variables)




  def _eval(self, command):
    try:
      result = self._matlab.eval(command, nargout=0)
    except:
      pass
    return result


  def _open(self, path):
    try:
      #open
      dirname = os.path.dirname(path)
      cd = self.commandBuilder.cd(dirname)
      model = os.path.basename(path)
      load_system = self.commandBuilder.load_system(model)
      command = cd + load_system
      result = self._matlab.eval(command, nargout=0)
      #addEjsSubsystem
      _load_model(model)
      
    except:
      return None
    return result

  def _load_model(self, model):
    command = self.commandBuilder.addEjsSubblock(model) + \
      self.commandBuilder.addPauseBlock(model) + \
      self.commandBuilder.set_param(model, "StartTime", "0") + \
      self.commandBuilder.set_param(model, "StopTime", "inf")
    self._matlab.eval(command)
    
    
  def _step(self, command):
    try:
      result = self._matlab.eval(command, nargout=0)
    except:
      return None
    return result
