from HttpServer import HttpServer
from rip.RIPOctave import RIPOctave

if __name__ == '__main__':
  HttpServer(
    host='127.0.0.1',
    port=8080,
    control=RIPOctave(
      name='Octave',
      description='An implementation of RIP to control Octave',
      authors='D. Garcia, J. Chacon',
      keywords='Octave, Raspberry PI, Robot',
    ),
  ).start()
