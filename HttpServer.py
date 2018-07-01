# - *- coding: utf- 8 - *-
'''
Created on 10/11/2015
Modified on 2018/07/01

@author: jcsombria
'''
import cherrypy
import ujson
import time
import os
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket, EchoWebSocket

from rip.RIPOctave import RIPOctave

class Root(object):
  exposed = True
  server = RIPOctave()

  @cherrypy.tools.accept(media='application/json')
  def POST(self):
    socket = cherrypy.request.body.fp
    message = socket.read()
    print(message)
    response = self.server.parse(message)
    print(response)
    return response.encode("utf-8")

if __name__ == '__main__':
  # Provides a relative log path from the original script path
  # instead from the invocation path
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
      'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
      'tools.sessions.on': True,
      'tools.response_headers.on': True,
      'tools.response_headers.headers': [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
      ],
      'tools.encode.on': True,
      'tools.encode.encoding': 'utf-8',
    },
  }

  cherrypy.quickstart(Root(), '/', config)
