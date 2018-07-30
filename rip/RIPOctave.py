'''
@author: jcsombria
'''
from oct2py import Oct2Py
import oct2py.io as oio
from rip.RIPGeneric import RIPGeneric
from random import random
import numpy as np
import scipy.io as sio
from PIL import Image
import string
from io import BytesIO, StringIO
import base64
import logging
#import pdb
import matplotlib as mpl
import matplotlib.image as mpimg
import time
import signal
import traceback

TIMEOUT = 60

# Logger Configuration
logger = logging.getLogger('oct2py')
logger.setLevel(logging.INFO)

log_stream = StringIO()
formatter = logging.Formatter('[%(asctime)s] - %(message)s')
ch = logging.StreamHandler(log_stream)
ch.setLevel(logging.INFO)

ch.setFormatter(formatter)
logger.addHandler(ch)

# Timeout exception for user code execution
class TimeoutError(Exception):
  pass

# Timeout handler for user code execution
def timeoutHandler(signum, frame):
  raise TimeoutError()

# Register signal handling for SIGALRM
signal.signal(signal.SIGALRM, timeoutHandler)

octave = Oct2Py(None, logger, TIMEOUT)

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

    octave.addpath(self.octavePath)
    octave.addpath(self.octavePath + '/kinect')
    octave.addpath(self.octavePath + '/arduino')
    octave.addpath(self.octavePath + '/user')
      
    try:
      logger.info("ENVIRONMENT SETUP...")
    except Exception as e:
      logger.error("init(): " + str(e))
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
    self.readables.append({
        'name':'octaveLog',
        'description':'String with log information',
        'type':'str',
        'min':'-Inf',
        'max':'Inf',
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
    logger.info("ENVIRONMENT SETUP COMPLETED")

  def __del__(self):
    octave.endSession()

  # This method will be invoked from HttpServer.SSE
  def start(self):
    try:
      logger.info("STARTING SERVER. EXECUTION TIMEOUT SET TO " + str(TIMEOUT) + " SECONDS.")
      super(RIPOctave, self).start()
      octave.robotSetup()
      octave.arduinoProcessInputs("K")
    except Exception as e:
      logger.error("start(): " + str(e))
      pass

  def set(self, expid, variables, values):
    '''
    Writes one or more variables to the workspace of the current Octave session
    '''
    #pdb.set_trace()
    #logger.debug("set(expid, variables, values): BEGIN " + str(variables))
    n = len(variables)
    #logger.debug("set(expid, variables, values) : (" + str(expid) + "(" + str(len(expid)) + "), " +  str(variables) + "(" + str(len(variables)) + "), " +  str(values) + "(" + str(len(values)) + ")")
    for i in range(n):
      try:
        logger.debug("set(): variable(" + str(i) + ") = " + str(variables[i]))

        # currentAction
        if(variables[i] == 'currentAction'):
          logger.debug("set(): octave.arduinoProcessInputs(" + str(values[i] + "): INIT"))
          logger.info('Sending command: ' + self.logAction(str(values[i])))
          octave.arduinoProcessInputs(values[i])
          logger.debug("set(): octave.arduinoProcessInputs(" + str(values[i] + "): END"))

        # octaveCode
        elif(variables[i] == 'octaveCode'):
          code = str(values).replace('\\', '\\\\').replace('\n','\\n').replace('\t','\\t').replace('\a', '\\a')
          code = code.replace('\b','\\f').replace('\r','\\r').replace('\v', '\\v')
          logger.debug("set(): octave.executeOctaveCode(): BEGIN: " + code)
          try:
            self.executeOctaveCode(code)
          except:
            pass
          logger.info("Code sent to robot.")
          logger.debug("set(): octave.executeOctaveCode(): END:")
      except Exception as e:
        logger.error("set() Error: " + str(e) + "; Traceback: " + str(traceback.format_exc()))
        
  def get(self, expid, variables):
    '''
    Retrieve one or more variables from the workspace of the current Octave session
    '''
    toReturn = {}
    logger.debug("get(expid, variables) : (" + str(expid) + "(" + str(len(expid)) + "), " +  str(variables) + "(" + str(len(variables)) + ")")
    n = len(variables)
    for i in range(n):
      name = variables[i]
      try:
        logger.debug("get(): octave.pull(" + str(name) + ")")
        toReturn[name] = octave.pull(name)
        logger.debug("get(): " + str(name) + " = " + str(toReturn[name]))
      except Exception as e:
        logger.error("get(): Error: " + str(e))
        pass
    return toReturn

  def getValuesToNotify(self):
    #pdb.set_trace()
    returnValue = self.previousMessage
    #logger.debug("getValuesToNotify(): PreviousValue = " + str(returnValue))
    try:
      logger.debug("getValuesToNotify(): octave.getDepthImage8()")
      #octave.getDepthImage8(0)
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
      logger.debug("getValuesToNotify(): octave.updateGlobals: BEGIN")
      result = octave.updateGlobals()
      logger.debug("getValuesToNotify(): octave.updateGlobals: END: " + str(result) + "(" + str(type(result)) + ")")
      #pdb.set_trace()
      if type(result) is list:
        logger.debug("getValuesToNotify(): type is list")
        pass
      elif type(result) is np.ndarray:
        logger.debug("getValuesToNotify(): type is np.ndarray and len(result) = 9")
        
        if type(result.item(0)) is float:
          self.TS = result.item(0)
          logger.debug("getValuesToNotify(TS): (" + str(result.item(0)) + ", " + str(type(result.item(0))) + ")")
        if type(result.item(1)) is float:
          self.DT = result.item(1)
          logger.debug("getValuesToNotify(DT): (" + str(result.item(1)) + ", " + str(type(result.item(1))) + ")")
        if type(result.item(2)) is float:
          self.CD = result.item(2)
          logger.debug("getValuesToNotify(CD): (" + str(result.item(2)) + ", " + str(type(result.item(2))) + ")")
        if type(result.item(3)) is float:
          self.CI = result.item(3)
          logger.debug("getValuesToNotify(CI): (" + str(result.item(3)) + ", " + str(type(result.item(3))) + ")")
        if type(result.item(4)) is float:
          self.MP = result.item(4)
          logger.debug("getValuesToNotify(MP): (" + str(result.item(4)) + ", " + str(type(result.item(4))) + ")")
        if type(result.item(5)) is float:
          self.MS = result.item(5)
          logger.debug("getValuesToNotify(MS): (" + str(result.item(5)) + ", " + str(type(result.item(5))) + ")")
        if type(result.item(6)) is float:
          self.IrF = result.item(6)
          logger.debug("getValuesToNotify(IrF): (" + str(result.item(6)) + ", " + str(type(result.item(6))) + ")")
        if type(result.item(7)) is float:
          self.IrR = result.item(7)
          logger.debug("getValuesToNotify(IrR): (" + str(result.item(7)) + ", " + str(type(result.item(7))) + ")")
        if type(result.item(8)) is float:
          self.IrL = result.item(8)
          logger.debug("getValuesToNotify(IrL): (" + str(result.item(8)) + ", " + str(type(result.item(8))) + ")")
      try:
        logger.debug("octave.getLastMessage(): BEGIN")
        msg = octave.getLastMessage()
        logger.debug("octave.getLastMessage(): END: (" + str(msg) + ", " + str(type(msg)) + ")")
        if isinstance(msg, oio.Cell) and msg.size == 2:
          self.TSM = int(msg.item(0))
          self.Mensaje = msg.item(1)
          logger.debug("getValuesToNotify(TSM): (" + str(self.TSM) + ", " + str(type(self.TSM)) + ")")
          logger.debug("getValuesToNotify(Mensaje): (" + str(self.Mensaje) + ", " + str(type(self.Mensaje)) + ")")
      except Exception as e:
        logger.error("getValuesToNotify(getLastMessage): ERROR : " + str(e))
        self.TSM = 0
        self.Mensaje = ""
        pass

      try:
        logger.debug("getValuesToNotify(imageArray): BEGIN")
        imageArray = octave.getKinectImageAsArray()
        if isinstance(imageArray, list) and len(imageArray) > 1:
        #if len(imageArray) > 1:
          logger.debug("getValuesToNotify(imageArray): octave.getKinectImageAsArray(): (" + str(len(imageArray)) + ", " + str(type(imageArray)) + ")")
          logger.debug("getValuesToNotify(imageArray): Image.fromArray: BEGIN")
          cmx = mpl.cm.get_cmap('prism')
          im = Image.fromarray(np.uint8(cmx(imageArray)*255))
          #im = Image.fromarray(np.uint8(imageArray))
          logger.debug("getValuesToNotify(imageArray): Image.fromArray: END")
          bufferedImage = BytesIO()
          logger.debug("getValuesToNotify(imageArray): Image.save: BEGIN")
          im.save(bufferedImage, format="PNG")
          logger.debug("getValuesToNotify(imageArray): Image.save: END")
          logger.debug("getValuesToNotify(imageArray): Image.toBase64: BEGIN")
          imstr = str(base64.b64encode(bufferedImage.getvalue())).split('\'')
          logger.debug("getValuesToNotify(imageArray): Image.toBase64: END: " + str(len(imstr)))
          if len(imstr) > 1:
            self.KinectImageBase64 = imstr[1]
            logger.debug("getValuesToNotify(imageArray): Received image: " + str(len(self.KinectImageBase64)))
          else:
            self.KinectImageBase64 = ''
            logger.warning("getValuesToNotify(imageArray): No image received")
      except Exception as e:
        self.KinectImageBase64= ''
        logger.error("getValuesToNotify(imageArray): Error recovering image: " + str(e))

      try:
        #self.Ready = octave.pull('Ready')
        self.Ready = 1
      except Exception as e:
        self.Ready = 0
        logger.error("getValuesToNotify(Ready): WARNING: " + str(e))
        pass

      self.showLogVariables()
      
      octaveLog = ""
      octaveLog = self.getLog()

      returnValue = [
        ['time', 'TS', 'DT', 'CD', 'CI', 'MP', 'MS','IrF','IrR','IrL', 'TSM', 'Mensaje', 'KinectImageBase64', 'Ready', 'octaveLog'],
        [self.sampler.lastTime(), self.TS, self.DT, self.CD, self.CI, self.MP, self.MS, self.IrF, self.IrR, self.IrL, self.TSM, self.Mensaje, self.KinectImageBase64, self.Ready, octaveLog]
      ]
      self.previousMessage = returnValue
      self.keepAlive()
    except Exception as e:
      returnValue = [['id', 'Mensaje'], [-1, str(e)]]
      logger.error("getValuesToNotify(general): Error executing method: " + str(e))
    return returnValue

  def getLog(self):
    result = ""
    try:
      result = log_stream.getvalue()
      log_stream.truncate(0)
      log_stream.seek(0)
      if result is None or len(result) == 0:
        result = ""
    except Exception as e:
      logger.error("getLog(): " + str(e))
    return result

  def executeOctaveCode(self, code):
    # Set timeout for code execution
    signal.alarm(TIMEOUT+10)
    try:
      octave.feval('executeOctaveCode', code, timeout=TIMEOUT)
    except TimeoutError as exc:
      logger.error("Timeout")
      self.start()
      pass
    except Exception as e:
      logger.error("executeOctaveCode(): " + str(e))
      self.start()
      pass
    finally:
      signal.alarm(0)

  def keepAlive(self):
    try:
      octave.arduinoProcessInputs('K')
    except:
      pass

  def showLogVariables(self):
    txt = "Received values: "
    txt += " [TS: " + "{:.0f}".format(self.TS) + ", "
    txt += "DT: " + "{:.0f}".format(self.DT) + ", "
    txt += "CD: " + "{:.0f}".format(self.CD) + ", "
    txt += "CI: " + "{:.0f}".format(self.CI) + ", "
    txt += "MP: " + "{:.0f}".format(self.MP) + ", "
    txt += "MS: " + "{:.0f}".format(self.MS) + ", "
    txt += "IrF: " + "{:.0f}".format(self.IrF) + ", "
    txt += "IrR: " + "{:.0f}".format(self.IrR) + ", "
    txt += "IrL: " + "{:.0f}".format(self.IrL) + "]"
    logger.info(txt)

  def logAction(self, action):
    return {
      'F' : 'MOVE FORWARD (MANUAL)',
      'B' : 'MOVE BACKWARDS (MANUAL)',
      'L' : 'TURN LEFT (MANUAL)',
      'R' : 'TURN RIGHT (MANUAL)',
      'P' : 'STOP ENGINES (MANUAL)',
      'K' : 'KEEP ALIVE'
    }.get(action, "NO ACTION")
