"""
  Config - data storage for merely bots
  Extends configparser with backups, defaults, saving and reloading
"""

from configparser import ConfigParser
import os, glob, shutil
import time


class Config(ConfigParser):
  """loads the config file automatically and ensures it's in a valid state"""
  def __init__(self, path:str = 'config'):
    """
    Custom init for merelybot configparser
    will always return a valid config object, even if the filesystem is broken
    """
    super().__init__()

    self.path = path
    self.file = os.path.join(self.path, "config.ini")
    self.template = os.path.join(self.path, "config.factory.ini")
    self.last_backup = 0

    self.load()

  def load(self):
    """ Verify file exists and load it """
    rebuild = False
    if not os.path.exists(self.path):
      print(
        f"WARNING: {self.path} missing - creating folder and generating bare-minimum defaults.",
        f"\nYou should consider writing or including a '{self.template}'"
      )
      rebuild = True
      os.makedirs(self.path)
    if not os.path.exists(self.file):
      if os.path.exists(self.template):
        print(f"WARNING: {self.file} missing - reverting to template config")
        shutil.copy(self.template, self.file)
      else:
        print(
          f"WARNING: {self.template} missing - resorting to bare-minimum defaults.",
          f"\nYou should consider writing or including a '{self.template}'"
        )
        rebuild = True
    if not rebuild:
      with open(self.file, 'r', encoding='utf-8') as f:
        ini = f.read()
        if ini.endswith('\n\n'):
          ConfigParser.read_string(self, ini)
        else:
          raise AssertionError(
            f"FATAL: {self.file} may have been in the process of saving during the last run!",
            "\nCheck your config file! There may be data loss."
          )

    # Ensure required sections exist and provide sane defaults
    # Generates config in case it's missing, but also updates old configs
    # Main section
    if 'main' not in self.sections():
      self.add_section('main')
    if 'token' not in self['main']:
      self['main']['token'] = ''
    if 'prefix_short' not in self['main']:
      self['main']['prefix_short'] = '/'
    if 'botname' not in self['main']:
      self['main']['botname'] = 'merely framework bot'
    if 'themecolor' not in self['main']:
      self['main']['themecolor'] = '0x0'
    if 'voteurl' not in self['main']:
      self['main']['voteurl'] = ''
    if 'tos_url' not in self['main']:
      self['main']['tos_url'] = ''
    if 'beta' not in self['main']:
      self['main']['beta'] = 'False'
    if 'ver' not in self['main']:
      self['main']['ver'] = ''
    if 'creator' not in self['main']:
      self['main']['creator'] = ''

    # Intents section
    if 'intents' not in self.sections():
      self.add_section('intents')
    if 'guilds' not in self['intents']:
      self['intents']['guilds'] = 'False'
    if 'members' not in self['intents']:
      self['intents']['members'] = 'False'
    if 'moderation' not in self['intents']:
      self['intents']['moderation'] = 'False'
    if 'emojis' not in self['intents']:
      self['intents']['emojis'] = 'False'
    if 'integrations' not in self['intents']:
      self['intents']['integrations'] = 'False'
    if 'webhooks' not in self['intents']:
      self['intents']['webhooks'] = 'False'
    if 'invites' not in self['intents']:
      self['intents']['invites'] = 'False'
    if 'voice_states' not in self['intents']:
      self['intents']['voice_states'] = 'False'
    if 'presences' not in self['intents']:
      self['intents']['presences'] = 'False'
    if 'message_content' not in self['intents']:
      self['intents']['message_content'] = 'False'
    if 'messages' not in self['intents']:
      self['intents']['messages'] = 'False'
    if 'reactions' not in self['intents']:
      self['intents']['reactions'] = 'False'
    if 'typing' not in self['intents']:
      self['intents']['typing'] = 'False'

    # Language section (babel)
    if 'language' not in self.sections():
      self.add_section('language')
    if 'default' not in self['language']:
      self['language']['default'] = 'en'
    if 'prefix' not in self['language']:
      self['language']['prefix'] = ''
    if 'contribute_url' not in self['language']:
      self['language']['contribute_url'] = ''

    # Extensions section
    if 'extensions' not in self.sections():
      self.add_section('extensions')
    self.save()

  def save(self):
    """ copy existing config to backups, save new config """
    # create a backup of the config (max 1 per hour)
    if self.last_backup < time.time() - (60*60):
      if not os.path.exists(os.path.join(self.path, 'config_history')):
        os.makedirs(os.path.join(self.path, 'config_history'))
      if os.path.isfile(self.file):
        oldfiles = glob.glob(
          os.path.join(self.path, 'config_history', 'config-'+time.strftime("%d-%m-%y ")+'*.ini')
        )
        shutil.copy(self.file, os.path.join(
          self.path,
          'config_history',
          'config-'+time.strftime("%d-%m-%y %H:%M.%S")+'.ini'
        ))
        for oldfile in oldfiles:
          os.remove(oldfile)

      self.last_backup = time.time()
    #TODO: autodelete all but one of each config history
    with open(self.file, 'w', encoding='utf-8') as f:
      ConfigParser.write(self, f)

  def reload(self):
    """ reset config and load it again """
    for section in self.sections():
      self.remove_section(section)
    self.load()
