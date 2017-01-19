'''
Created on 20/10/2015

@author: jcsombria
'''
import os.path

from jsonrpc.JsonRpcServer import JsonRpcServer
from app.MatlabConnector import CommandBuilder, MatlabConnector

import matlab.engine

class SimulinkConnector(MatlabConnector):
  '''
  classdocs
  '''

  def __init__(self):
    '''
    Constructor
    '''
    super().__init__()
    self.startRequired = True


#  def _connect(self):
#    self._matlab = matlab.engine.start_matlab('-desktop')
#    return True


#  def _disconnect(self):
#    self._matlab.quit()


#  def _set(self, variables, values):
#    if isinstance(variables, list):
#      size = len(variables)
#      for i in range(size):
#        try:
#          name, value = variables[i], values[i]
#          self._matlab.workspace[name] = value
#        except:
#          pass
#    else:
#      try:
#        name, value = variables, values
#        self._matlab.workspace[name] = value
#      except:
#        pass
#      

#  def _get(self, variables):
#    if self._shouldGetResultAsDict():
#      result = {}
#      for name in variables:
#        try:
#          value = self._matlab.workspace[name]
#          result[name] = value
#        except:
#          pass
#    else:
#      result = []
#      for name in variables:
#        try:
#          value = self._matlab.workspace[name]
#          result.append(value)
#        except:
#          pass
#    return result


#  def _shouldGetResultAsDict(self):
#    return False


#  def _eval(self, command):
#    try:
#      result = self._matlab.eval(command, nargout=0)
#    except:
#      pass
#    return result



  def open(self, path):
    try:
      #open
      dirname = os.path.dirname(path)
      filename = os.path.basename(path)
      modelname = os.path.splitext(filename)[0]
      self.model = {
        'path': dirname,
        'file': filename,
        'name': modelname,
      }
      load = \
        self.commandBuilder.cd(self.model['path']) + \
        self.commandBuilder.load_system(self.model['file'])
      result = self.eval(load)
      #addEjsSubsystem
      self._load_model(self.model['name'])
    except:
      return "Matlab Not Connected"
    return result

  def _load_model(self, model):
    command = self.commandBuilder.add_ejs_subblock(model) + \
      self.commandBuilder.add_pause_block(model) + \
      self.commandBuilder.set_param(model, "StartTime", "0") + \
      self.commandBuilder.set_param(model, "StopTime", "inf")
    self.eval(command)
    

  def step(self, dt):
    model = self.model['name']
    if (self.startRequired):
      command = self._start()
      self.startRequired = False
    else:
      command = self._step()
    try:
      self.eval(command)
      self._waitForPauseSimulink()
    except:
      print('Error in step()')
      return None

  def _start(self):
    return self.commandBuilder.set_param(model, "SimulationCommand", "start")

  def _step(self):
    return \
self.commandBuilder.set_param(model, "SimulationCommand","update") + \
self.commandBuilder.set_param(model, "SimulationCommand", "continue") + \
"EjsSimulationStatus='unknown';"


  
  def _waitForPauseSimulink(self):
    isPaused = False    
    while not isPaused:
      isPaused = self._isSimulinkPaused()

  def _isSimulinkPaused(self):
    command = self.commandBuilder.is_model_paused(self.model['name'])
    self.eval(isModelPausedCommand)
    isPaused = self.get("smlkstatus")
    print(isPaused)
    return isPaused


#from app.SimulinkConnector import SimulinkConnector
#simulink = SimulinkConnector()
#simulink.connect()
#simulink.open('Examples/FirstOrder/FirstOrder.mdl')
#simulink.set(['u'], [1.0])
#simulink.step(1.0)
