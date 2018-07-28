'''
@author: jcsombria
'''
from oct2py import octave
from rip.RIPGeneric import RIPGeneric
from random import random
import numpy as np
from PIL import Image
import string
from io import BytesIO
import base64
import logging
#import pdb
import matplotlib as mpl
import matplotlib.image as mpimg
import traceback

LOG_FILENAME = '/var/log/robot/RIPOctave.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

class RIPOctave(RIPGeneric):
  '''
  RIP Octave Adapter
  '''
  def __init__(self, name='Octave', description='An implementation of RIP to control Octave', authors='J. Chacon', keywords='Octave'):
    '''
    Constructor
    '''
    super().__init__(name, description, authors, keywords)
    self.octavePath = '/home/pi/workspace/robot/octave'
    self.dataArray = []
    self.messageArray = {}
    self.TS = 0.0
    self.DT = 0.0
    self.CD = 0.0
    self.CI = 0.0
    self.MP = 0.0
    self.MS = 0.0
    self.IrF = 0.0
    self.IrR = 0.0
    self.IrL = 0.0
    self.TSM = 0.0
    self.Mensaje = ""
    self.previousMessage = []
    self.KinectImageBase64 = ""
    self.Ready = 0

    octave.eval('global dataArray;')
    octave.eval('global messageArray;')
    octave.eval('global TS;')
    octave.eval('global DT;')
    octave.eval('global CD;')
    octave.eval('global CI;')
    octave.eval('global MP;')
    octave.eval('global MS;')
    octave.eval('global IrF;')
    octave.eval('global IrR;')
    octave.eval('global IrL;')
    octave.eval('global Ready;')
    octave.eval('global octaveCode;')
    octave.eval('global debugLevel;')
    
    octave.push("Ready", 0)
    octave.push("debugLevel", 5)

    try:
      self.initSession()
    except Exception as e:
      logging.error("initSession(): " + str(e))
      pass

    self.readables.append({
        'name':'TS',
        'description':'Timestamp of the reading',
        'type':'long',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'DT',
        'description':'Time from the previous lecture',
        'type':'long',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'CD',
        'description':'Number of counts from right decoder',
        'type':'int',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'CI',
        'description':'Number of counts from left decoder',
        'type':'int',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'MP',
        'description':'Engine status (0=off, 1=on)',
        'type':'int',
        'min':'0',
        'max':'1',
        'precision':'0'
      })
    self.readables.append({
        'name':'MS',
        'description':'Laser status (0=off, 1=on)',
        'type':'int',
        'min':'0',
        'max':'1',
        'precision':'0'
      })
    self.readables.append({
        'name':'IrF',
        'description':'Distance (in cm) readed by frontal sensor',
        'type':'int',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'IrR',
        'description':'Distance (in cm) readed by right sensor',
        'type':'int',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'IrL',
        'description':'Distance (in cm) readed by left sensor',
        'type':'int',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'TSM',
        'description':'Timestamp of the message reading',
        'type':'long',
        'min':'-Inf',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'Mensaje',
        'description':'Last readed message',
        'type':'str',
        'min':'0',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'KinectImageBase64',
        'description':'Image retrieved from Kinect in Base64 format',
        'type':'str',
        'min':'0',
        'max':'Inf',
        'precision':'0'
      })
    self.readables.append({
        'name':'Ready',
        'description':'Checks wether or not the robot is ready to operate',
        'type':'int',
        'min':'0',
        'max':'1',
        'precision':'0'
      })
    self.writables.append({
        'name':'currentAction',
        'description':'Sets an action to perform in the robot: D(-255,255), I(-255,255),P,K,F,B,L,R,S,U',
        'type':'str',
        'min':'0',
        'max':'Inf',
        'precision':'0'
    })
    self.writables.append({
        'name':'octaveCode',
        'description':'Sets a string with octave code to be executed in the server',
        'type':'str',
        'min':'0',
        'max':'Inf',
        'precision':'0'
    })

  def __del__(self):
    octave.endSession()

  # This method will be invoked from HttpServer.SSE
  def start(self):
    try:
      octave.addpath(self.octavePath)
      octave.robotSetup()
      octave.arduinoProcessInputs("K")
    except Exception as e:
      logging.error("start(): " + str(e))
      pass

  def set(self, expid, variables, values):
    '''
    Writes one or more variables to the workspace of the current Octave session
    '''
    #pdb.set_trace()
    #logging.debug("set(expid, variables, values): BEGIN " + str(variables))
    n = len(variables)
    #logging.debug("set(expid, variables, values) : (" + str(expid) + "(" + str(len(expid)) + "), " +  str(variables) + "(" + str(len(variables)) + "), " +  str(values) + "(" + str(len(values)) + ")")
    for i in range(n):
      try:
        logging.debug("set(): variable(" + str(i) + ") = " + str(variables[i]))
        if(variables[i] == 'currentAction'):
          logging.debug("set(): octave.arduinoProcessInputs(" + str(values[i] + "): INIT"))
          octave.arduinoProcessInputs(values[i])
          logging.debug("set(): octave.arduinoProcessInputs(" + str(values[i] + "): END"))
        elif(variables[i] == 'octaveCode'):
          code = str(values).replace('\\', '\\\\').replace('\n','\\n').replace('\t','\\t').replace('\a', '\\a')
          code = code.replace('\b','\\f').replace('\r','\\r').replace('\v', '\\v')
          logging.debug("set(): octave.executeOctaveCode(): BEGIN: " + code)
          octave.executeOctaveCode(code)
          logging.debug("set(): octave.executeOctaveCode(): END:")
      except Exception as e:
        logging.error("set() Error: " + str(e) + "; Traceback: " + str(traceback.format_exc()))
        
  def get(self, expid, variables):
    '''
    Retrieve one or more variables from the workspace of the current Octave session
    '''
    toReturn = {}
    logging.debug("get(expid, variables) : (" + str(expid) + "(" + str(len(expid)) + "), " +  str(variables) + "(" + str(len(variables)) + ")")
    n = len(variables)
    for i in range(n):
      name = variables[i]
      try:
        logging.debug("get(): octave.pull(" + str(name) + ")")
        toReturn[name] = octave.pull(name)
        logging.debug("get(): " + str(name) + " = " + str(toReturn[name]))
      except Exception as e:
        logging.error("get(): Error: " + str(e))
        pass
    return toReturn

  def getValuesToNotify(self):
    #pdb.set_trace()
    returnValue = self.previousMessage
    #logging.debug("getValuesToNotify(): PreviousValue = " + str(returnValue))
    try:
      logging.debug("getValuesToNotify(): octave.getDepthImage8()")
      octave.getDepthImage8()
    except:
      pass
    try:
      self.TS = 0
      self.DT = 0
      self.CD = 0
      self.CI = 0
      self.MP = 0
      self.MS = 0
      self.IrF = 0
      self.IrR = 0
      self.IrL = 0
      logging.debug("getValuesToNotify(): octave.updateGlobals: BEGIN")
      result = octave.updateGlobals()
      logging.debug("getValuesToNotify(): octave.updateGlobals: END: " + str(result) + "(" + str(type(result)) + ")")
      #pdb.set_trace()
      if type(result) is list:
        logging.debug("getValuesToNotify(): type is list")
        pass
      elif type(result) is np.ndarray:
        logging.debug("getValuesToNotify(): type is np.ndarray and len(result) = 9")
        
        if type(result.item(0)) is float:
          self.TS = result.item(0)
          logging.debug("getValuesToNotify(TS): (" + str(result.item(0)) + ", " + str(type(result.item(0))) + ")")
        if type(result.item(1)) is float:
          self.DT = result.item(1)
          logging.debug("getValuesToNotify(DT): (" + str(result.item(1)) + ", " + str(type(result.item(1))) + ")")
        if type(result.item(2)) is float:
          self.CD = result.item(2)
          logging.debug("getValuesToNotify(CD): (" + str(result.item(2)) + ", " + str(type(result.item(2))) + ")")
        if type(result.item(3)) is float:
          self.CI = result.item(3)
          logging.debug("getValuesToNotify(CI): (" + str(result.item(3)) + ", " + str(type(result.item(3))) + ")")
        if type(result.item(4)) is float:
          self.MP = result.item(4)
          logging.debug("getValuesToNotify(MP): (" + str(result.item(4)) + ", " + str(type(result.item(4))) + ")")
        if type(result.item(5)) is float:
          self.MS = result.item(5)
          logging.debug("getValuesToNotify(MS): (" + str(result.item(5)) + ", " + str(type(result.item(5))) + ")")
        if type(result.item(6)) is float:
          self.IrF = result.item(6)
          logging.debug("getValuesToNotify(IrF): (" + str(result.item(6)) + ", " + str(type(result.item(6))) + ")")
        if type(result.item(7)) is float:
          self.IrR = result.item(7)
          logging.debug("getValuesToNotify(IrR): (" + str(result.item(7)) + ", " + str(type(result.item(7))) + ")")
        if type(result.item(8)) is float:
          self.IrL = result.item(8)
          logging.debug("getValuesToNotify(IrL): (" + str(result.item(8)) + ", " + str(type(result.item(8))) + ")")
      try:
        logging.debug("octave.getLastMessage(): BEGIN")
        msg = octave.getLastMessage()
        logging.debug("octave.getLastMessage(): END: (" + str(msg) + ", " + str(type(msg)) + ")")
        if msg.size == 2:
          self.TSM = int(msg.item(0))
          self.Mensaje = msg.item(1)
          logging.debug("getValuesToNotify(TSM): (" + str(self.TSM) + ", " + str(type(self.TSM)) + ")")
          logging.debug("getValuesToNotify(Mensaje): (" + str(self.Mensaje) + ", " + str(type(self.Mensaje)) + ")")
      except Exception as e:
        logging.error("getValuesToNotify(getLastMessage): ERROR : " + str(e))
        self.TSM = 0
        self.Mensaje = ""
        pass

      try:
        logging.debug("getValuesToNotify(imageArray): BEGIN")
        imageArray = octave.getKinectImageAsArray()
        logging.debug("getValuesToNotify(imageArray): octave.getKinectImageAsArray(): (" + str(len(imageArray)) + ", " + str(type(imageArray)) + ")")
        if len(imageArray) > 1:
          logging.debug("getValuesToNotify(imageArray): Image.fromArray: BEGIN")
          cmx = mpl.cm.get_cmap('prism')
          im = Image.fromarray(np.uint8(cmx(imageArray)*255))
          #im = Image.fromarray(np.uint8(imageArray))
          logging.debug("getValuesToNotify(imageArray): Image.fromArray: END")
          bufferedImage = BytesIO()
          logging.debug("getValuesToNotify(imageArray): Image.save: BEGIN")
          im.save(bufferedImage, format="PNG")
          logging.debug("getValuesToNotify(imageArray): Image.save: END")
          logging.debug("getValuesToNotify(imageArray): Image.toBase64: BEGIN")
          imstr = str(base64.b64encode(bufferedImage.getvalue())).split('\'')
          logging.debug("getValuesToNotify(imageArray): Image.toBase64: END: " + str(len(imstr)))
          if len(imstr) > 1:
            self.KinectImageBase64 = imstr[1]
            logging.debug("getValuesToNotify(imageArray): Received image: " + str(len(self.KinectImageBase64)))
          else:
            self.KinectImageBase64 = ''
            logging.warning("getValuesToNotify(imageArray): No image received")
      except Exception as e:
        self.KinectImageBase64= ''
        logging.error("getValuesToNotify(imageArray): Error recovering image: " + str(e))

      try:
        self.Ready = octave.pull('Ready')
      except Exception as e:
        self.Ready = 0
        logging.error("getValuesToNotify(Ready): ERROR: " + str(e))

      returnValue = [
        ['time', 'TS', 'DT', 'CD', 'CI', 'MP', 'MS','IrF','IrR','IrL', 'TSM', 'Mensaje', 'KinectImageBase64', 'Ready'],
        [self.sampler.lastTime(), self.TS, self.DT, self.CD, self.CI, self.MP, self.MS, self.IrF, self.IrR, self.IrL, self.TSM, self.Mensaje, self.KinectImageBase64, self.Ready]
      ]
      self.previousMessage = returnValue
    except Exception as e:
      returnValue = [['id', 'Mensaje'], [-1, str(e)]]
      logging.error("getValuesToNotify(general): Error executing method: " + str(e))
    return returnValue
