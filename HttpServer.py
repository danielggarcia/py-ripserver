'''
Created on 10/11/2015

@author: jcsombria
'''
import cherrypy
import ujson
import time
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
  cherrypy.config.update({
    'server.socket_port': 2055,
    'log.access_file' : './log/access.log',
    'log.errors_file' : './log/error.log'
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
