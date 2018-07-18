'''
@author: jcsombria
'''
import time

from jsonrpc.JsonRpcServer import JsonRpcServer
from jsonrpc.JsonRpcBuilder import JsonRpcBuilder
from rip.RIPMeta import *

builder = JsonRpcBuilder()

class RIPGeneric(JsonRpcServer):
  '''
  RIP Server - Reference Implementation
  '''

  def __init__(self, name='RIP Generic', description='Generic RIP Server Implementation.', authors='J. Chacon', keywords='RIP'):
    '''
    Constructor
    '''
    super().__init__(name, description)

    self.authors = authors
    self.keywords = keywords
    self.ssePeriod = 0.5
    self.sseRunning = False
    self._running = False
    self.readables = [{
        'name':'time',
        'description':'Server time in seconds',
        'type':'float',
        'min':'0',
        'max':'Inf',
        'precision':'0'
      },
    ]
    self.writables = []
    self.addMethods({
      'get': { 'description': 'To read server variables',
        'params': { 'expId': 'string', 'variables': '[string]' },
        'implementation': self.get,
      },
      'set': { 'description': 'To write server variables',
        'params': { 'expId': 'string', 'variables': '[string]', 'values':'[]' },
        'implementation': self.set,
      },
    })

  def start(self):
    '''
    Iniatilizes the server. Any code meant to be run at init should be here.
    '''
    if not self.sseRunning:
      self.sseRunning = True
      self.sampler = Sampler(self.ssePeriod)
    self._running = True

  @property
  def running(self):
    return self._running

  @running.setter
  def running(self):
    pass

  def info(self, address='127.0.0.1:8080'):
    '''
    Retrieve the experience's info
    '''
    try:
      info = self.info_string
    except:
      info = self.build_info(address)
      self.info_string = info
    return info

  def build_info(self, address):
    '''
    Generate the experience's info string
    '''
    info = RIPServerInfo(
      self.name,
      self.description,
      authors=self.authors,
      keywords=self.keywords
    )
    readables = RIPVariablesList(
      list_=self.readables,
      methods=[self.buildSSEGetInfo(address), self.buildPOSTGetInfo(address)],
      read_notwrite=True
    )
    writables = RIPVariablesList(
      list_=self.writables,
      methods=[self.buildPOSTSetInfo(address)],
      read_notwrite=False
    )
    meta = RIPMetadata(info, readables, writables)
    return str(meta)

  def buildSSEGetInfo(self, address):
    return RIPMethod(
      url='%s/RIP/SSE' % address,
      description='Suscribes to an SSE to get regular updates on the servers\' variables',
      type_='GET',
      params=[
        RIPParam(name='Accept',required='no',location='header',value='application/json'),
        RIPParam(name='expId',required='yes',location='query',type_='string'),
        RIPParam(name='variables',required='no',location='query',type_='array',subtype='string'),
      ],
      returns='text/event-stream',
      example='%s/RIP/SSE?expId=%s' % (address, self.name),
    )

  def buildPOSTGetInfo(self, address):
    elements = [{'description': 'Experience id','type': 'string'},
    {'description': 'Name of variables to be retrieved','type': 'array','subtype': 'string'}]
    return RIPMethod(
      url='%s/RIP/POST' % address,
      description='Sends a request to retrieve the value of one or more servers\' variables on demand',
      type_='POST',
      params=[
        RIPParam(name='Accept',required='no',location='header',value='application/json'),
        RIPParam(name='Content-Type',required='yes',location='header',type_='application/json'),
        RIPParam(name='jsonrpc',required='yes',type_='string',location='body',value='2.0'),
        RIPParam(name='method',required='yes',type_='string',location='body',value='get'),
        RIPParam(name='params',required='yes',type_='array',location='body',elements=elements),
        RIPParam(name='id',required='yes',type_='int',location='body'),
      ],
      returns='application/json',
      example={ '%s/RIP/POST' % address: {
        'headers': {'Accept': 'application/json','Content-Type': 'application/json'},
        'body': {'jsonrpc':'2.0', 'method':'get', 'params':['%s' % self.name, [r['name'] for r in self.readables]], 'id':'1'}
      }}
    )

  def buildPOSTSetInfo(self, address):
    elements = [{'description': 'Experience id','type': 'string'},
    {'description': 'Name of variables to write','type': 'array','subtype': 'string'},
    {'description': 'Value for variables','type': 'array','subtype': 'mixed'}]
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
      '%s/RIP/POST' % address: {
        'headers': {'Accept': 'application/json','Content-Type': 'application/json'},
        'body': {'jsonrpc':'2.0','method':'set','params':['%s' % self.name,[w['name'] for w in self.writables],['val' for w in self.writables]],'id':'1'}
      }
    }
    return RIPMethod(
      url='%s/RIP/POST' % address,
      description='Sends a request to retrieve the value of one or more servers\' variables on demand',
      type_='POST',
      params=params_post_set,
      returns='application/json',
      example=example_post_set
    )

  def set(self, expid, variables, values):
    '''
    Sends one or more variables to the server
    '''
    pass

  def get(self, expid, variables):
    '''
    Retrieve one or more variables from the server
    '''
    pass

  def nextSample(self, wrap='data: %s\n\n'):
    '''
    Retrieve the next periodic update
    '''
    if not self.sseRunning:
      self.sseRunning = True
      self.sampler = Sampler(self.ssePeriod)

    while self.sseRunning:
      self.sampler.wait()
      try:
        toReturn = self.getValuesToNotify()
      except:
        toReturn = 'ERROR'
      response = builder.response(result=toReturn, request_id='1')
      yield 'data: %s\n\n' % ujson.dumps(response)

  def getValuesToNotify(self):
    return [
      [ 'time' ],
      [ self.sampler.lastTime() ]
    ]

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
