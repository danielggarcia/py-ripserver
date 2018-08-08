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
import os
import traceback
import shutil

TIMEOUT = 60
OCTAVEPATH = '/home/pi/workspace/robot/octave'
CACHEBASEPATH = '/var/robot/cache/cache_'
RESULTMATFILEPATH = '/var/robot/mat/robot.mat'
LOGFILEPATH = '/var/robot/log/RIPOctave.log'
PIDFILEPATH = '/tmp/py_ripserver_'
PNGIMAGEPATH='/var/robot/tmp/depthimage.png'
LOCKFILE='/var/robot/tmp/.lock'

# Logger Configuration
logger = logging.getLogger('oct2py')
logger.setLevel(logging.INFO)

log_stream = StringIO()
formatter = logging.Formatter('[%(asctime)s] - %(message)s')
ch = logging.StreamHandler(log_stream)
ch.setLevel(logging.INFO)

ch.setFormatter(formatter)
logger.addHandler(ch)

fh = logging.FileHandler(LOGFILEPATH)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

# Timeout exception for user code execution
class TimeoutError(Exception):
  pass

# Timeout handler for user code execution
def timeoutHandler(signum, frame):
  raise TimeoutError()

# Reads and increases by one a value written in the file /tmp/py_ripserver_PID
# The watchdog will check if the value has been increased. If not, it will reset
# the server process
def watchDog(signum, frame):
  try:
    logger.debug("watchDog(): entering handler")
    currentPid = os.getpid()
    pidfile = PIDFILEPATH + str(currentPid)
    logger.debug("PID FILE: " + pidfile)
    with open(pidfile, 'r') as f:
      currentValue = int(f.read())
      logger.debug("watchDog(): read value: " + str(currentValue))
    currentValue += 1
    with open(pidfile, 'w') as f:
      f.write(str(currentValue))
      logger.debug("watchDog(): write value: " + str(currentValue))
    pass
  except Exception as e:
    logger.error("watchDog(): Error checking watchdog file: " + str(e))
  
# Register signal handling for SIGALRM
signal.signal(signal.SIGALRM, timeoutHandler)

# Register signal for SIGUSR2 (watchdog)
signal.signal(signal.SIGUSR2, watchDog)
  
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
    self.currentIteration = 0
    self.resultFilePath = ''
    self.userId = '0000'
    self.currentSessionTimestamp = ''

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
    octave.eval('global cachePath;')
    octave.eval('global userId;')
    
    octave.push("Ready", 0)
    octave.push("debugLevel", 2)
    
    octave.addpath(OCTAVEPATH)
    octave.addpath(OCTAVEPATH + '/kinect')
    octave.addpath(OCTAVEPATH + '/arduino')
    octave.addpath(OCTAVEPATH + '/user')
      
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
    self.readables.append({
        'name':'matFile',
        'description':'Contents of the .mat file',
        'type':'Object',
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
    self.writables.append({
        'name':'userId',
        'description':'Sets the user ID in order to filter which data may be accesed',
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
      octave.push('debugLevel', 2)
      # Function 'cacheData' appends every reading from arduino and kinect in a variable within the mat file provided
      # in global variable 'cachePath'.
      # This function is invoked from three octave functions: updateData(), Kinect.getImageUint8() and Kinect.getImageUint16().
      # The cached data avoids data loss in case that connection is interrupted.
      # The octave function getLastCachedDataFilePath() will provide the last cached file, whilst saveEnvironment() will
      # make use of that file to generate a .mat file with all the data.
      self.currentSessionTimestamp = "{:.0f}".format(octave.generateTimeStamp())
      self.resultFilePath = CACHEBASEPATH + self.userId + "_" + self.currentSessionTimestamp + '.mat'
      if os.path.exists(RESULTMATFILEPATH):
        os.remove(RESULTMATFILEPATH)
      octave.push("cachePath", self.resultFilePath)
      octave.push("userId", self.userId)
      octave.robotSetup()
      time.sleep(3)
      octave.arduinoProcessInputs("K")
    except Exception as e:
      logger.error("start(): " + str(e))
      pass

  def set(self, expid, variables, values):
    '''
    Writes one or more variables to the workspace of the current Octave session
    '''
    n = len(variables)
    for i in range(n):
      try:
        logger.debug("set(): variable(" + str(i) + ") = " + str(variables[i]))

        # currentAction
        if(variables[i] == 'currentAction'):
          logger.info('Sending command: ' + self.logAction(str(values[i])))
          octave.arduinoProcessInputs(values[i])
        # octaveCode
        elif(variables[i] == 'octaveCode'):
          code = str(values).replace('\\', '\\\\').replace('\n','\\n').replace('\t','\\t').replace('\a', '\\a')
          code = code.replace('\b','\\f').replace('\r','\\r').replace('\v', '\\v')
          try:
            self.executeOctaveCode(code)
          except:
            pass
          logger.info("Code sent to robot.")
        elif(variables[i] == 'userId'):
          if type(values) is list and len(values) == 1:
            logger.info('Setting user ID to: ' + str(values[i]))
            self.userId = str(values[i])
            self.resultFilePath = CACHEBASEPATH + self.userId + "_" + self.currentSessionTimestamp + '.mat'
            octave.push('userId', self.userId)
            octave.push('cachePath', self.resultFilePath)
      except Exception as e:
        logger.error("set() Error: " + str(e) + "; Traceback: " + str(traceback.format_exc()))
        
  def get(self, expid, variables):
    '''
    Retrieve one or more variables from the workspace of the current Octave session
    '''
    toReturn = {}
    #logger.debug("get(expid, variables) : (" + str(expid) + "(" + str(len(expid)) + "), " +  str(variables) + "(" + str(len(variables)) + ")")
    n = len(variables)
    for i in range(n):
      name = variables[i]
      try:
        # TODO: Intentar obtener el contenido del fichero .mat, que tiene formato binario
        #with open(self.resultFilePath) as f: toReturn['matFile'] = f.read()
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
      logger.debug("getValuesToNotify(): getDepthImageBase64(): BEGIN")
      self.currentIteration += 1
      if self.currentIteration >= 3:
        self.currentIteration = 0
        self.KinectImageBase64 = self.getDepthImageBase64()
    except:
      pass
    try:
      result = octave.updateGlobals()
      self.getGlobalVariables(result)
      try:
        self.Ready = octave.isKinectReady()
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
      if str(e) == 'list index out of range':
        pass
      else:
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

  def getGlobalVariables(self, result):
    self.resetGlobals()
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

  def resetGlobals(self):
    self.TS = 0
    self.DT = 0
    self.CD = 0
    self.CI = 0
    self.MP = 0
    self.MS = 0
    self.IrF = 0
    self.IrR = 0
    self.IrL = 0

  def getDepthImageBase64(self):
    depthImageBase64 = ''
    try:
      logger.debug("getDepthImageBase64(imageArray): BEGIN")
      retrieved = octave.getDepthImage()

      if retrieved == 1 and os.path.exists(PNGIMAGEPATH):
        bufferedImage = BytesIO()
        try:
          for i in range(20):
            if os.path.exists(LOCKFILE):
                time.sleep(0.1)
            else:
                break
            if i == 20:
                os.remove(LOCKFILE)
          im = Image.open(PNGIMAGEPATH)
        except Exception as e:
          logger.error("getDepthImageBase64() Image.open: Error recovering image: " + str(e))
          raise e
        try:  
          im.save(bufferedImage, format="PNG")
        except Exception as e:
          logger.error("getDepthImageBase64() Image.save: Error recovering image: " + str(e))
          raise e
        imstr = str(base64.b64encode(bufferedImage.getvalue())).split('\'')
        if len(imstr) > 1:
          depthImageBase64 = imstr[1]
          logger.debug("getDepthImageBase64(imageArray): Received image: " + str(len(self.KinectImageBase64)))
        else:
          depthImageBase64 = ''
          logger.warning("getDepthImageBase64(imageArray): No image received")
    except Exception as e:
      depthImageBase64 = ''
      logger.error("getDepthImageBase64(imageArray): Error recovering image: " + str(e))
    finally:
      if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)
    return depthImageBase64

  def logAction(self, action):
    return {
      'F' : 'MOVE FORWARD (MANUAL)',
      'B' : 'MOVE BACKWARDS (MANUAL)',
      'L' : 'TURN LEFT (MANUAL)',
      'R' : 'TURN RIGHT (MANUAL)',
      'P' : 'STOP ENGINES (MANUAL)',
      'K' : 'KEEP ALIVE'
    }.get(action, "NO ACTION")
