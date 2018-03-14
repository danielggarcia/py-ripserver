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

  def _connect(self):
    return True


  def _disconnect(self):
    pass


  def _set(self, variables, values):
    for i in range(0, len(variables)):
      name = variables[i]
      octave[name] = values


  def _get(self, variables):
    toReturn = {}
    for i in range(0, len(variables)):
      name = variables[i]
      toReturn[name] = octave[name]

    return toReturn


  def _eval(self, command):
    try:
      result = octave.eval(command)
    except:
      pass
    return result
