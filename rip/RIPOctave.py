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
import _thread
import subprocess

DEBUG = False
DEFAULT_EXECUTION_TIMEOUT = 180
OCTAVEPATH = '/opt/robot/octave'
USERCODEPATH='/opt/robot/octave/user/usercode.m'
CACHEBASEPATH = '/var/robot/cache/cache_'
RESULTMATFILEPATH = '/var/robot/mat/robot.mat'
LOGFILEPATH = '/var/robot/log/RIPOctave.log'
PIDFILEPATH = '/tmp/py_ripserver_'
KINECT_PNGIMAGEPATH='/var/robot/tmp/depthimage.png'
ARUCO_PNGIMAGEPATH='/var/robot/tmp/arucomarker.png'
KINECT_LOCKFILE='/var/robot/tmp/.kinect_lock'
ARUCO_LOCKFILE='/var/robot/tmp/.aruco_lock'

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

def watchDog(signum, frame):
  '''
  Reads and increases by one a value written in the file /tmp/py_ripserver_PID
  The watchdog will check if the value has been increased. If not, it will reset
  the server process
  '''
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
    self.CeilingImageBase64 = ""
    self.Ready = 0
    self.currentIteration = 0
    self.resultFilePath = ''
    self.userId = '0000'
    self.currentSessionTimestamp = ''
    self.captureFrames = False
    self.octave = self.octaveSetup()

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
    self.readables.append({
        'name':'octaveCode',
        'description':'Gets a string with octave code to be executed in the server',
        'type':'str',
        'min':'0',
        'max':'Inf',
        'precision':'0'
    })
    self.readables.append({
        'name':'CeilingImageBase64',
        'description':'Image retrieved from ceiling camera in Base64 format',
        'type':'str',
        'min':'0',
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

  #def __del__(self):
  #  subprocess.Popen(['/bin/bash', '-c', "nohup bash -c 'sleep 5 && watchdog restart' 2> /dev/null &"])
  #  subprocess.Popen(['/bin/bash', '-c', "nohup bash -c 'sleep 4 && rm /var/robot/tmp' 2> /dev/null &"])
    
  #  #octave.endSession()

  # This method will be invoked from HttpServer.SSE
  def start(self):
    '''
    Method that will be invoked when the user logs in, and that performs the following actions:
        - Generates a cache file identified by the user ID obtained from EjsS and by the logon time stamp.
        - Invokes the Octave robotSetup method, which initializes the streaming, Arduino, ArUco and Kinect services.
        - Makes a first data request to the robot to obtain its initial state.
    '''
    try:
      logger.info("STARTING SERVER. EXECUTION TIMEOUT SET TO " + str(DEFAULT_EXECUTION_TIMEOUT) + " SECONDS.")
      super(RIPOctave, self).start()
      # Function 'cacheData' appends every reading from arduino and kinect in a variable within the mat file provided
      # in global variable 'cachePath'.
      # This function is invoked from the following octave functions: 
      #   updateData(): saves information to 'robotData' array
      #   getDepth(): saves information to 'robotDepthImages' and 'robotDepthImageTimestamps' arrays
      #   getDepthCm(): saves information to 'robotDepthImagesCm' and 'robotDepthImageTimestampsCm' arrays
      #   getMarkers(): saves information to 'cornerData', 'rotationData' and 'translationData' arrays
      # The cached data avoids data loss in case that connection is interrupted.
      # The octave function getLastCachedDataFilePath() will provide the last cached file, whilst saveEnvironment() will
      # make use of that file to generate a .mat file with all the data.
      self.currentSessionTimestamp = "{:.0f}".format(self.octave.generateTimeStamp())
      self.resultFilePath = CACHEBASEPATH + self.userId + "_" + self.currentSessionTimestamp + '.mat'
      if os.path.exists(RESULTMATFILEPATH):
        os.remove(RESULTMATFILEPATH)
      self.octave.push("cachePath", self.resultFilePath)
      self.octave.push("userId", self.userId)
      #logger.info("USERID: " + repr(self.userId))
      self.octave.robotSetup()
      time.sleep(10)
    except Exception as e:
      logger.error("start(): " + str(e))
      pass

  def set(self, expid, variables, values):
    '''
    Assigns a value to a variable.
    This method is invocable from the EjsS interface and serves to transmit information to the robot from the client side.
    The three possible variables that are handled in this method are the following:
         - currentAction: corresponds to an action of the robot ('K','F', 'B', 'R', 'L') and is sent to Arduino by invoking the arduinoProcessInputs() method.
         - octaveCode: corresponds to the code that must be sent and executed in the robot, so the executeOctaveCode() method is invoked.
        - userId: corresponds to the user identifier, which will be used to make the session unique and establish the cache file where the values captured by the user will be stored.
    '''
    n = len(variables)
    for i in range(n):
      try:
        logger.debug("set(): variable(" + str(i) + ") = " + str(variables[i]))

        # currentAction
        if(variables[i] == 'currentAction'):
          for j in range(60):
            try:
              if(len(values) >= i+1) and (values[i] == 'Q'):
                logger.info('Shutting down session')
                subprocess.Popen(['/bin/bash', '-c', "nohup sudo robotwatchdog reset 2> /dev/null &"])
                time.sleep(5)
                logger.info('DONE')
                return
              if (j == 0) and (len(values) >= i+1):
                logger.info('Sending command: ' + self.logAction(str(values[i])))
              else: 
                logger.warning('Esperando comunicación con Arduino... (' + repr(j) + ')')
              if (len(values) >= i+1):
                self.octave.eval("arduinoProcessInputs('" + values[i] + "')")
                self.captureFrames = True
              break
            except Exception as e:
              if DEBUG:
                logger.error("set(currentAction) Error: " + str(e) + "; Traceback: " + str(traceback.format_exc()))
              time.sleep(1)
              pass
        # octaveCode
        elif(variables[i] == 'octaveCode'):

          numSecs = DEFAULT_EXECUTION_TIMEOUT
          try:
            code = values
            if(code.find('setExecutionTimeout(') == 0):
              try:
                numSecs = int(code[code.find('(') + 1:code.find(')')])
                if numSecs > 900:
                  numSecs = 900
                logger.info("Timeout changed to " + str(numSecs))
              except Exception as e:
                numSecs = 60
                pass
                
            variables[i] = ""
            _thread.start_new_thread(self.executeOctaveCode, (code, numSecs))
            #self.executeOctaveCode(code, numSecs)
            
          except Exception as e:
            logger.warn("Error while processing robot code: "+ str(e))
            pass
          logger.info("Code sent to robot.")
        elif(variables[i] == 'userId'):
          if type(values) is list and len(values) == 1:
            #logger.info('Setting user ID to: ' + str(values[i]))
            self.userId = str(values[i])
            self.resultFilePath = CACHEBASEPATH + self.userId + "_" + self.currentSessionTimestamp + '.mat'
            self.octave.push('userId', self.userId)
            self.octave.push('cachePath', self.resultFilePath)
      except Exception as e:
        logger.error("set() Error: " + str(e) + "; Traceback: " + str(traceback.format_exc()))
        
  def get(self, expid, variables):
    '''
    Retrieves one or more variables from the workspace of the current Octave session
    '''
    toReturn = {}
    #logger.debug("get(expid, variables) : (" + str(expid) + "(" + str(len(expid)) + "), " +  str(variables) + "(" + str(len(variables)) + ")")
    n = len(variables)
    for i in range(n):
      name = variables[i]
      try:
        logger.info("get(): INIT")
        logger.debug("get(): octave.pull(" + str(name) + ")")
        toReturn[name] = self.octave.pull(name)
        logger.debug("get(): " + str(name) + " = " + str(toReturn[name]))
      except Exception as e:
        logger.error("get(): Error: " + str(e))
        pass
    logger.info("get(): returning " + repr(toReturn))
    return toReturn

  def getValuesToNotify(self):
    '''
    This method is invoked from EjsS periodically to obtain real-time information on the robot's status.
    The function retrieves the latest sensor values from octave by invoking the updateGlobals method and 
    recovers a depth image from the Kinect device and a augmented image from the ceiling via the ceiling webcam 
    in one out of every three invocations of the method in base64 format so that the experience is not computatively penalized. 
    You then get the system log from the last call. Finally, it stores the results in two arrays that simulate a 
    set of key value pairs and contain the following elements: 
    time, TS, DT, CD, CI, MP, MS, IrF, TSM, Message, KinectImageBase64, CeilingImageBase64, Ready, octaveLog.
    '''
    returnValue = self.previousMessage
    self.Ready = self.octave.isKinectReady()
    self.octave.eval("arduinoProcessInputs('D0I0', 0.2)")
    logger.debug("getValuesToNotify(): getDepthImageBase64(): BEGIN")
    if self.captureFrames == True:
      try:
        if self.Ready:
          self.KinectImageBase64 = self.getDepthImageBase64()
        self.CeilingImageBase64 = self.getCeilingImageBase64()
        self.captureFrames = False
      except Exception as e:
        self.Ready = 0
        logger.error("getValuesToNotify(Ready): WARNING: " + str(e))
        pass

    try:
      result = self.octave.updateGlobals()
      self.getGlobalVariables(result)

      if (len(self.previousMessage) == 2) and (len(self.previousMessage[1]) == 16) and (self.TS != self.previousMessage[1][1]):
        self.showLogVariables()

      octaveLog = self.getLog()

      returnValue = [
        ['time', 'TS', 'DT', 'CD', 'CI', 'MP', 'MS','IrF','IrR','IrL', 'TSM', 'Mensaje', 'KinectImageBase64', 'CeilingImageBase64', 'Ready', 'octaveLog'],
        [self.sampler.lastTime(), self.TS, self.DT, self.CD, self.CI, self.MP, self.MS, self.IrF, self.IrR, self.IrL, self.TSM, self.Mensaje, self.KinectImageBase64, self.CeilingImageBase64, self.Ready, octaveLog]
      ]
      self.previousMessage = returnValue
    except Exception as e:
      returnValue = [['id', 'Mensaje'], [-1, str(e)]]
      if str(e) == 'list index out of range':
        pass
      else:
        logger.error("getValuesToNotify(general): Error executing method: " + str(e))
    return returnValue

  def octaveSetup(self):
    o = Oct2Py(None, logger, DEFAULT_EXECUTION_TIMEOUT)

    o.eval('global dataArray;')
    o.eval('global messageArray;')
    o.eval('global TS;')
    o.eval('global DT;')
    o.eval('global CD;')
    o.eval('global CI;')
    o.eval('global MP;')
    o.eval('global MS;')
    o.eval('global IrF;')
    o.eval('global IrR;')
    o.eval('global IrL;')
    o.eval('global Ready;')
    o.eval('global octaveCode;')
    o.eval('global debugLevel;')
    o.eval('global cachePath;')
    o.eval('global userId;')
    
    o.push("Ready", 0)

    if DEBUG:
      o.push("debugLevel", 5)
    else:
      o.push("debugLevel", 2)
    
    #o.genpath(OCTAVEPATH)
    o.addpath(OCTAVEPATH)
    o.addpath(OCTAVEPATH + '/common')
    o.addpath(OCTAVEPATH + '/kinect')
    o.addpath(OCTAVEPATH + '/arduino')
    o.addpath(OCTAVEPATH + '/aruco')
    o.addpath(OCTAVEPATH + '/user')

    return o

  def getLog(self):
    '''
    Extracts the information stored by the system log, extracts the lines and filters them for later delivery to the user.
    '''
    result = ""
    logData = ""
    try:
      result = log_stream.getvalue()
      log_stream.truncate(0)
      log_stream.seek(0)

      resultLines = result.splitlines()
      for line in resultLines:
        if "Stream 70" in line:
          continue
        elif "ans =" in line:
          continue
        else:
          logData = logData + line + "\n"

      if logData is None or len(logData) == 0:
        logData = ""
    except Exception as e:
      logger.error("getLog(): " + str(e))
    return logData

  def executeOctaveCode(self, code, timeout=DEFAULT_EXECUTION_TIMEOUT):
    '''
    Writes the code code in the usercode.m file in the /octave/user folder of the robot and have Octave run it.
    If after timeout seconds the execution of the code has not finished, the execution is automatically aborted.
    '''

    # Set timeout for code execution
    signal.alarm(DEFAULT_EXECUTION_TIMEOUT+10)
    try:
      logger.info("Sending code to robot with timeout = " + str(timeout) + ": \n\n" + repr(code) + "\n\n")
      with open(USERCODEPATH, 'w') as f:
        code = "try\n" + code
        code = code + "\ncatch err\n    if (debugLevel >= 2); fprintf('[ERROR] executeOctaveCode(): %s\\n', err.message); fflush(stdout); endif;\npause(0.1);\nend_try_catch"
        f.write(code)
      self.octave.feval('executeOctaveCode', '', timeout)
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
      #self.octave.arduinoProcessInputs('K')
      self.octave.eval("arduinoProcessInputs('D0I0', 0.2)")
      self.KinectImageBase64 = self.getDepthImageBase64()
      self.CeilingImageBase64 = self.getCeilingImageBase64()
    except:
      pass

  def showLogVariables(self):
    '''
    Stores in the system log the information of the attributes TS, DT, CD, CI, MP, MS, IrF, TSM in a human readable format.
    '''
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
    if self.TS > 0:
      logger.info(txt)

  def getGlobalVariables(self, result):
    '''
    Stores in the TS, DT, CD, CI, MP, MS, IrF, IrF, IrR and IrL variables the values of the array result, 
    which must have been retrieved from Octave using the updateGlobals function.
    '''
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
      msg = self.octave.getLastMessage()
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
    '''
    Sets to 0 the local data retrieved from Arduino
    '''
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
    '''
    Invokes the getDepthImage() method of Octave, generating an image from the depth matrix obtained by Kinect.
    It is then encoded in base64 format using the getImageBase64() method to facilitate 
    its delivery to EjsS using the getValuesToNotify() method.
    '''
    depthImageBase64 = ''
    try:
      logger.debug("getDepthImageBase64(imageArray): BEGIN")
      retrieved = self.octave.getDepthImage()

      if retrieved == 1 and os.path.exists(KINECT_PNGIMAGEPATH):
        try:
          depthImageBase64 = self.getImageBase64(KINECT_PNGIMAGEPATH, KINECT_LOCKFILE)
        except Exception as e:
          logger.error("getDepthImageBase64() Image.open: Error recovering image: " + str(e))
          raise e
    except Exception as e:
      depthImageBase64 = ''
      logger.error("getDepthImageBase64(imageArray): Error recovering image: " + str(e))
    finally:
      if os.path.exists(KINECT_LOCKFILE):
        os.remove(KINECT_LOCKFILE)
    return depthImageBase64

  def getCeilingImageBase64(self):
    '''
    Invokes Octave's getMarkerInfo() method, capturing the webcam from the ceiling and augmenting 
    it with the information from the detected markers.
    It is then encoded in base64 format for easy delivery to EjsS using the getValuesToNotify() method.
    '''
    ceilingImageBase64 = ''
    try:
      logger.debug("getCeilingImageBase64(imageArray): BEGIN")
      retrieved = self.octave.getMarkerInfo(1)

      if os.path.exists(ARUCO_PNGIMAGEPATH):
        try:
          ceilingImageBase64 = self.getImageBase64(ARUCO_PNGIMAGEPATH, ARUCO_LOCKFILE)
        except Exception as e:
          logger.error("getCeilingImageBase64() Image.open: Error recovering image: " + str(e))
          raise e
    except Exception as e:
      ceilingImageBase64 = ''
      logger.error("getCeilingImageBase64(imageArray): Error recovering image: " + str(e))
    finally:
      if os.path.exists(ARUCO_LOCKFILE):
        os.remove(ARUCO_LOCKFILE)
    return ceilingImageBase64

  def getImageBase64(self, imagePath, lockFilePath):
    '''
    Checks that the lockFilePath file does not exist and then loads the image stored in imagePath 
    and converts it to the base64 string format.
    The lockFilePath file is a lock file generated by the services responsible for capturing images 
    at the beginning of the process, and is deleted when the image is ready for use.
    '''
    imageBase64 = ''
    try:
      logger.debug("getImageBase64(imageArray): BEGIN")
      retrieved = self.octave.getDepthImage()

      if retrieved == 1 and os.path.exists(imagePath):
        bufferedImage = BytesIO()
        try:
          for i in range(20):
            if os.path.exists(lockFilePath):
                time.sleep(0.1)
            else:
                break
            if i == 20:
                os.remove(lockFilePath)
          im = Image.open(imagePath)
        except Exception as e:
          logger.error("getImageBase64() Image.open: Error recovering image: " + str(e))
          raise e
        try:  
          im.save(bufferedImage, format="PNG")
        except Exception as e:
          logger.error("getImageBase64() Image.save: Error recovering image: " + str(e))
          raise e
        imstr = str(base64.b64encode(bufferedImage.getvalue())).split('\'')
        if len(imstr) > 1:
          imageBase64 = imstr[1]
          logger.debug("getImageBase64(imageArray): Received image: " + str(len(imstr)))
        else:
          imageBase64 = ''
          logger.warning("getImageBase64(imageArray): No image received")
    except Exception as e:
      imageBase64 = ''
      logger.error("getImageBase64(imageArray): Error recovering image: " + str(e))
    finally:
      if os.path.exists(lockFilePath):
        os.remove(lockFilePath)
    return imageBase64

  def logAction(self, action):
    '''
    Transforms a mnemonic interpetable by arduino ('K','P','D100', etc.) into a string that 
    can be interpreted by a human being for inclusion in the system log.
    '''
    return {
      'F' : 'MOVE FORWARD (MANUAL)',
      'B' : 'MOVE BACKWARDS (MANUAL)',
      'L' : 'TURN LEFT (MANUAL)',
      'R' : 'TURN RIGHT (MANUAL)',
      'P' : 'STOP ENGINES (MANUAL)',
      'K' : 'KEEP ALIVE'
    }.get(action, "NO ACTION")

