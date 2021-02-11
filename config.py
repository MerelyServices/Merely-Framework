from configparser import ConfigParser
from shutil import copy
from os import path,makedirs
import time

class Config(ConfigParser):
  path = "config/"
  file = "config/config.ini"
  template = "config/config.template.ini"

  def __init__(self):
    super()
    if not (path.exists(self.path) and path.exists(self.template)):
      raise Exception("./config or ./config/config.factory.ini missing")
    if not (path.exists(self.file) and path.isfile(self.file)):
      copy(self.template, self.file)
    with open(self.file, encoding='utf-8') as f:
      self.read(f)
  
  def save(self):
    if not path.exists(self.path+'config_history/'+time.strftime("%m-%y")):
      makedirs(self.path+'config_history/'+time.strftime("%m-%y"))
    copy(self.file, self.path+'config_history/'+time.strftime("%m-%y")+'/config-'+time.strftime("%H:%M.%S-%d-%m-%y")+'.ini')
    with open(self.file, encoding='utf-8') as f:
      self.write(f)