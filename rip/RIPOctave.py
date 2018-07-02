'''
Created on 20/10/2015

@author: jcsombria
'''
import os.path
import time

from jsonrpc.JsonRpcServer import JsonRpcServer
from jsonrpc.JsonRpcBuilder import JsonRpcBuilder
from oct2py import octave
from rip.RIPMeta import *

builder = JsonRpcBuilder()

class RIPOctave(JsonRpcServer):
  '''
  RIP Octave Adapter
  '''

  def __init__(self, name='RIP Octave', description='An implementation of RIP for Octave'):
    '''
    Constructor
    '''
    super().__init__(name, description)

    self.ssePeriod = 0.5
    self.sseRunning = False
    info = {
      'get': {
        'description': 'To read server variables',
        'params': {
          'expId': 'string',
          'variables': '[string]',
        },
        'implementation': self.get,
      },
      'set': {
        'description': 'To write server variables',
        'params': {
          'expId': 'string',
          'variables': '[string]',
          'values':'[]',
        },
        'implementation': self.set,
      },
    }
    for method in info:
      try:
        implementation = info[method].get('implementation')
        self.on(method, info[method], implementation)
      except:
        print('[WARNING] Ignoring invalid method')

  def info(self):
    '''
    Retrieve the experience's info
    '''
    try:
      info = self.info_string
    except:
      info = self.build_info()
      self.info_string = info
    return info

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


  def eval(self, command):
    try:
      result = octave.eval(command)
    except:
      pass
    return result


  def nextSample(self, wrap='data: %s\n\n'):
    '''
    Retrieve the next periodic update
    '''
    if not self.sseRunning:
      self.sseRunning = True
      octave.push('x', 0)
      self.sampler = Sampler(self.ssePeriod)

    while self.sseRunning:
      self.sampler.wait()
      try:
        variables = self.get('Robot', ['x'])
        toReturn = [
          [ "time", "x" ],
          [ self.sampler.lastTime(), variables['x'] ]
        ]
      except:
        toReturn = "ERROR"
      response = builder.response(result=toReturn, request_id='1')
      yield 'data: %s\n\n' % ujson.dumps(response)


  def build_info(self):
    '''
    Generate the experience's info string
    '''
    params_sse_get = [
      RIPParam(name='Accept',required='no',location='header',value='application/json'),
      RIPParam(name='expId',required='yes',location='query',type_='string'),
      RIPParam(name='variables',required='no',location='query',type_='array',subtype='string'),
    ]
    sse_get = RIPMethod(
      url='10.192.38.68:8080/RIP/SSE', 
      description='Suscribes to an SSE to get regular updates on the servers\' variables',
      type_='GET',
      params=params_sse_get,
      returns='text/event-stream',
      example='10.192.38.68:8080/RIP/SSE?expId=TestOK'
    )

    elements = [{"description": "Experience id","type": "string"},
    {"description": "Name of variables to be retrieved","type": "array","subtype": "string"}]
    params_post_get = [
      RIPParam(name='Accept',required='no',location='header',value='application/json'),
      RIPParam(name='Content-Type',required='yes',location='header',type_='application/json'),
      RIPParam(name='jsonrpc',required='yes',type_='string',location='body',value="2.0"),
      RIPParam(name='method',required='yes',type_='string',location='body',value='get'),
      RIPParam(name='params',required='yes',type_='array',location='body',elements=elements),
      RIPParam(name='id',required='yes',type_='int',location='body'),
    ]
    example_post_get = {
      "10.192.38.68:8080/RIP/POST": {
        "headers": {"Accept": "application/json","Content-Type": "application/json"},
        "body": {"jsonrpc":"2.0","method":"get","params":["TestOK",["var1","var2"]],"id":"1"}
      }
  }
    post_get = RIPMethod(
      url='10.192.38.68:8080/RIP/POST', 
      description='Sends a request to retrieve the value of one or more servers\' variables on demand',
      type_='POST',
      params=params_post_get,
      returns='application/json',
      example=example_post_get
    )

    elements = [{"description": "Experience id","type": "string"},
    {"description": "Name of variables to write","type": "array","subtype": "string"},
    {"description": "Value for variables","type": "array","subtype": "mixed"}]
    params_post_set = [
      RIPParam(name='Accept',required='no',location='header',value='application/json'),
      RIPParam(name='Content-Type',required='yes',location='header',type_='application/json'),
      RIPParam(name='jsonrpc',required='yes',type_='string',location='body',value='2.0'),
      RIPParam(name='method',required='yes',type_='string',location='body',value='set'),
      RIPParam(name='params',required='yes',type_='array',location='body',elements=elements),
      RIPParam(name='id',required='yes',type_='int',location='body'),
      RIPParam(name='variables',required='no',location='query',type_='array',subtype='string'),
    ]
    example_post_set = {
      "10.192.38.68:8080/RIP/POST": {
        "headers": {"Accept": "application/json","Content-Type": "application/json"},
        "body": {"jsonrpc":"2.0","method":"set","params":["TestOK",["var1","var2"],["val1","val2"]],"id":"1"}
      }
    }
    post_set = RIPMethod(url='10.192.38.68:8080/RIP/POST', 
      description='Sends a request to retrieve the value of one or more servers\' variables on demand',
      type_='POST', params=params_post_set, returns='application/json', example=example_post_set)


    info = RIPServerInfo('Robot', 'Raspberry Pi - Robot Server', authors='J. Chacon', keywords='Robot, Raspberry PI')
    readables = RIPVariablesList(list_=[],methods=[sse_get,post_get],read_notwrite=False)
    writables = RIPVariablesList(list_=[],methods=[post_set],read_notwrite=True)
    meta = RIPMetadata(info, readables, writables)

    return str(meta)
    
    
    
class Sampler(object):

  def __init__(self, period):
    self.Ts = period
    self.reset()

  def wait(self):
    self.last = self.time
    self.time = time.time() - self.t0
    self.next = self.time / self.Ts + self.Ts
    interval = self.Ts - self.time % self.Ts
    time.sleep(interval)

  def reset(self):
    self.t0 = time.time()
    self.time = 0
    self.last = 0
    self.next = self.Ts

  def delta(self):
    return self.time - self.last
  
  def lastTime(self):
    return self.last
