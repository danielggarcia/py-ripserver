# CommandBuilder
# author: Jesus Chacon <jcsombria@gmail.com>
#
# Copyright (C) 2014 Jesus Chacon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os.path
import matlab.engine

class MatlabConnector(object):

  def __init__(self):
    self.matlab = None
    self.commandBuilder = CommandBuilder() 


  def connect(self):
    if(self.matlab == None):
      self.matlab = matlab.engine.start_matlab('-desktop')

  def disconnect(self):
    self.matlab.quit()


  def set(self, variables, values):
    if isinstance(variables, list):
      size = len(variables)
      for i in range(size):
        try:
          name, value = variables[i], values[i]
          self.matlab.workspace[name] = value
        except:
          pass
    else:
      try:
        name, value = variables, values
        self.matlab.workspace[name] = value
      except:
        pass
      

  def get(self, variables):
    if self._shouldGetResultAsDict():
      result = {}
      for name in variables:
        try:
          value = self.matlab.workspace[name]
          result[name] = value
        except:
          pass
    else:
      result = []
      for name in variables:
        try:
          value = self.matlab.workspace[name]
          result.append(value)
        except:
          pass
    return result

  def _shouldGetResultAsDict(self):
    return False

  def eval(self, command):
    try:
      result = self.matlab.eval(command, nargout=0)
    except:
      pass
    return result




class CommandBuilder(object):

  # Command to add the EJS subblock to a Simulink model
  addEjsSubblockCommand = "Ejs_sub_name=['%s','/','Ejs_sub_','%s']; \n" \
    + "add_block('built-in/subsystem',Ejs_sub_name); \n" \
    + "XY=get_param('%s','location'); \n" \
    + "height=XY(4)-XY(2); \n" \
    + "width=XY(3)-XY(1); \n" \
    + "sXY=[width/2-16,height-48,width/2+16,height-16]; \n" \
    + "ico1=['image(ind2rgb(['];\n" \
    + "ico2=['4,4,4,4,4,4,4,4,4,4,4,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,4,4,4,4,4,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,4,4,4,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,4,4,4,4,4,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,4,4,2,2,2,2,3,3,3,3,3,3,3,3,3,3,3,4,4,4,4,4,4,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,4,4,2,2,2,2,3,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,4,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,4,4,4,4,4,4,4,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,4,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,4,4,4,4,4,4,4,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,4,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,4,4,4,4,4,4,4,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,4,2,2,2,2,3,3,3,3,3,3,3,3,3,3,3,4,4,2,2,2,2,3,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,4,2,2,2,2,3,4,4,4,4,4,4,4,4,4,4,4,4,2,2,2,2,3,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,2,2,2,2,3,4,4,4,4,4,4,4,4,4,4,4,4,4,2,2,2,2,3,4;',...\n" \
    + "'4,4,4,4,4,4,4,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,4,4,4,2,2,2,2,3,4;',...\n" \
    + "'4,4,4,4,4,4,4,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,4,4,2,2,2,2,2,4,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,4,4,2,2,2,2,3,4,4;',...\n" \
    + "'4,4,4,4,4,4,2,2,2,2,2,2,2,2,3,4,4,4,4,4,4,4,4,4,2,2,2,2,2,4,4,4;',...\n" \
    + "'4,4,4,4,4,2,2,2,2,2,2,2,2,2,2,3,4,4,4,4,4,4,4,4,1,1,1,1,3,4,4,4;',...\n" \
    + "'4,4,4,4,2,2,2,2,2,2,2,2,2,2,2,2,4,4,4,4,4,4,4,4,1,1,1,1,3,4,4,4;',...\n" \
    + "'4,4,4,2,2,2,2,2,3,3,3,2,2,2,2,2,3,4,4,4,4,4,4,1,1,1,1,1,3,4,4,4;',...\n" \
    + "'4,4,4,2,2,2,2,3,4,4,4,4,4,2,2,2,2,4,4,4,4,4,4,1,1,1,1,1,3,4,4,4;',...\n" \
    + "'4,4,4,2,2,2,2,3,4,4,4,4,4,3,3,3,3,4,4,4,4,4,4,1,1,1,1,1,3,4,4,4;',...\n" \
    + "'4,4,4,2,2,2,2,2,4,4,4,4,4,2,2,2,2,3,4,4,4,4,4,2,2,2,2,3,4,4,4,4;',...\n" \
    + "'4,4,4,4,2,2,2,2,2,2,4,4,4,2,2,2,2,3,3,4,4,4,2,2,2,2,2,3,4,4,4,4;',...\n" \
    + "'4,4,4,4,4,1,1,1,1,1,1,1,4,2,2,2,2,2,2,2,2,2,2,2,2,2,3,4,4,4,4,4;',...\n" \
    + "'4,4,4,4,4,4,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,3,4,4,4,4,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,3,4,4,4,4,4,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,4,4,2,2,2,2,2,3,3,3,3,3,3,3,3,3,3,4,4,4,4,4,4,4;',...\n" \
    + "'4,4,4,4,4,4,4,4,4,4,4,2,2,2,2,3,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4;',...\n" \
    + "'4,2,2,2,2,4,4,4,4,4,4,2,2,2,3,3,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4;',...\n" \
    + "'4,2,2,2,2,4,4,4,4,4,4,2,2,2,3,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4;',...\n" \
    + "'4,2,2,2,2,2,2,2,2,2,2,2,2,2,3,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4;',...\n" \
    + "'4,4,2,2,2,2,2,2,2,2,2,2,2,3,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4;',...\n" \
    + "'4,4,4,2,2,2,2,2,2,2,2,2,3,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4;',...\n" \
    + "'4,4,4,4,3,3,3,3,3,3,3,3,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4;'];\n" \
    + "ico3=['],[1 1 0;1 0 0;0 0 0;1 1 1]))'];\n" \
    + "set_param(Ejs_sub_name,'position',sXY,'ShowName','off','MaskDisplay',[ico1,ico2,ico3],'MaskIconFrame','off');\n" \
    + "add_block('built-in/clock',[Ejs_sub_name,'/Clock']); \n" \
    + "set_param([Ejs_sub_name,'/Clock'],'DisplayTime','on','Position', [30, 75, 70, 95]); \n" \
    + "add_block('built-in/toworkspace',[Ejs_sub_name,'/timeToWS']); \n" \
    + "set_param([Ejs_sub_name,'/timeToWS'],'VariableName','Ejs_time','Position',[150, 75, 200, 95],'Buffer','1'); \n" \
    + "add_line(Ejs_sub_name,'Clock/1','timeToWS/1');"

  commands = {
    'cd': "cd ('%s');",
		'load_system': "load_system ('%s');",
    'set_param': "set_param ('%s', '%s', '%s');",
    'get_param': "get_param ('%s', '%s');",
    'addEjsSubblockCommand': addEjsSubblockCommand,
  }

  def cd(self, path):
    return self.commands['cd'] % (path,)

  def load_system(self, model):
    return self.commands['load_system'] % (model,)

  def set_param(self, model, param, value):
    '''
    Matlab command 'set_param' to modify a param of a Simulink model.
      model the model to be modified
      param the param to set
      value the new value of the param
    '''
    return self.commands['set_param'] % (model, param, value)

  def is_model_paused(self, model, statusvar='smlkstatus'):
    status = self.get_param(model, "SimulationStatus").rstrip(';')
    getStatusCommand = "%s = strcmp(%s,'paused');" % (statusvar, status,)
    return getStatusCommand

  def get_param(self, model, param):
    return self.commands['get_param'] % (model, param)

  def add_ejs_subblock(self, model):
    return self.commands['addEjsSubblockCommand'] % (model, model, model);
	
  def add_pause_block(self, model):
    return "add_block('built-in/ground',[Ejs_sub_name,'/Gr1']); \n" \
      + "set_param([Ejs_sub_name,'/Gr1'],'Position', [30, 135, 70, 155]); \n" \
      + "add_block('built-in/matlabfcn',[Ejs_sub_name,'/Pause Simulink']); \n" \
      + "comando=['set_param(''" + model + "'',','''','SimulationCommand','''',',','''','Pause','''',')']; \n" \
      + "set_param([Ejs_sub_name,'/Pause Simulink'],'MATLABFcn',comando,'OutputWidth','0','Position',[150, 125, 200, 165]); \n" \
      + "add_line(Ejs_sub_name,'Gr1/1','Pause Simulink/1'); \n"
	
  def add_fixed_step_block(self, model, step):
    return  "set_param('" + model + "','FixedStep','" + step + "');" \
      + "add_block('built-in/digital clock',[Ejs_sub_name,'/fixedStep']);\n" \
      + "set_param([Ejs_sub_name,'/fixedStep'],'Position', [30, 135, 70, 155],'sampletime','" + step + "'); \n" \
      + "add_block('built-in/matlabfcn',[Ejs_sub_name,'/Pause Simulink']); \n" \
      + "comando=['set_param(''" + model + "'',','''','SimulationCommand','''',',','''','Pause','''',')']; \n" \
      + "set_param([Ejs_sub_name,'/Pause Simulink'],'MATLABFcn',comando,'OutputWidth','0','Position',[150, 125, 200, 165]); \n" \
      + "add_line(Ejs_sub_name,'fixedStep/1','Pause Simulink/1'); \n"
	

