'''
@author: jcsombria
'''
import cherrypy
import os

from rip.RIPMeta import *
from rip.RIPOctave import RIPOctave

class RIPOctaveHttpServer(object):
  '''
  RIP Server implementation
  '''
  exposed = True
  octave = RIPOctave()

  @cherrypy.expose
  def index(self, expId=None):
    '''
    GET - Retrieve the list of experiences or information about a specific experience
    '''
    if expId is not None:
      response = self.octave.info()
    else:
      response = self.info()
    return response.encode("utf-8")

  @cherrypy.expose
  def SSE(self, expId=None):
    '''
    SSE - Connect to an experience's SSE channel to receive periodic updates
    '''
    cherrypy.response.headers['Content-Type'] = 'text/event-stream'
    cherrypy.response.headers['Cache-Control'] = 'no-cache'
    cherrypy.response.headers['Connection'] = 'keep-alive'

    return self.octave.nextSample()
  SSE._cp_config = {'response.stream': True}

  @cherrypy.expose
  @cherrypy.tools.accept(media='application/json')
  def POST(self):
    '''
    POST - JSON-RPC control commands (get/set)
    '''
    socket = cherrypy.request.body.fp
    message = socket.read()
    response = self.octave.parse(message)
    return response.encode("utf-8")

  def info(self):
    '''
    Build server info string
    '''
    params_get_info = [
      RIPParam(name='Accept',required='no',location='header',value='application/json'),
      RIPParam(name='expId',required='no',location='query',type_='string'),
    ]
    get_info = RIPMethod(url='10.192.38.71:8080/RIP', 
      description='Retrieves information (variables and methods) of the experiences in the server',
      type_='GET', params=params_get_info, returns='application/json', example='http://10.192.38.71:8080/RIP?expId=TestOK')
    experiences = [{'id':'Robot'}]
    meta = RIPExperienceList(experiences, [get_info])
    return str(meta)

# --------------------------------------------------------------------------------------------------

if __name__ == '__main__':
  base_dir = os.path.dirname(os.path.realpath(__file__))
  log_dir = os.path.join(base_dir, 'log')
  access_log_file = os.path.join(log_dir, 'access.log')
  error_log_file = os.path.join(log_dir, 'error.log')
  cherrypy.config.update({
    'server.socket_port': 2055,
    'log.access_file' : access_log_file,
    'log.errors_file' : error_log_file
  })
  config = {
    '/': {
      'tools.response_headers.on': True,
      'tools.response_headers.headers': [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
      ],
      'tools.encode.on': True,
      'tools.encode.encoding': 'utf-8',
    },
  }
  cherrypy.quickstart(RIPOctaveHttpServer(), '/RIP', config)

