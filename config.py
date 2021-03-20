from configparser import ConfigParser
from shutil import copy
from os import path,makedirs
import time, pprint


""" Loads the config file automatically """
class Config(ConfigParser):
  path = "config/"
  file = "config/config.ini"
  template = "config/config.factory.ini"

  def __init__(self):
    ConfigParser.__init__(self)
    if not (path.exists(self.path) and path.exists(self.template)):
      raise Exception(f"./{self.path} or ./{self.template} missing")
    if not (path.exists(self.file) and path.isfile(self.file)):
      copy(self.template, self.file)
    ConfigParser.read(self, self.file, encoding='utf-8')
  
  def save(self):
    if not path.exists(self.path+'config_history/'+time.strftime("%m-%y")):
      makedirs(self.path+'config_history/'+time.strftime("%m-%y"))
    copy(self.file, self.path+'config_history/'+time.strftime("%m-%y")+'/config-'+time.strftime("%H:%M.%S-%d-%m-%y")+'.ini')
    with open(self.file, 'w', encoding='utf-8') as f:
      ConfigParser.write(self, f)