from configparser import ConfigParser
from typing import Union
import discord
from discord.ext import commands
import os, re

class Babel():
  path = 'babel/'
  langs = {}

  def __init__(self, config:ConfigParser):
    self.config = config
    self.baselang = config.get('language', 'default', fallback='en')

    if os.path.isfile(self.path):
      os.remove(self.path)
    if not os.path.exists(self.path) or not os.path.exists(self.path+self.baselang+'.ini'):
      raise Exception(f"The path {self.path} must exist and contain a complete {self.baselang}.ini.")
    
    for langfile in os.scandir(self.path):
      langfile = langfile.name
      if langfile[-4:] == '.ini':
        langname = langfile[:-4]
        self.langs[langname] = ConfigParser(comment_prefixes='@', allow_no_value=True) # create a configparser that should preserve comments
        self.langs[langname].read(self.path+langfile)
        if 'meta' not in self.langs[langname]:
          self.langs[langname].add_section('meta')
        self.langs[langname].set('meta', 'language', langname)
        with open(self.path+langfile, 'w', encoding='utf-8') as f:
          self.langs[langname].write(f)

  def resolve_lang(self, ctx:Union[commands.Context, tuple], debug=False):
    langs = []
    dbg_origins = []
    if isinstance(ctx, commands.Context):
      authorid = ctx.author.id
      guildid = ctx.guild.id if isinstance(ctx.channel, discord.abc.GuildChannel) else None
    else:
      authorid = ctx[0]
      guildid = ctx[1] if len(ctx)>1 else None
    
    if str(authorid) in self.config['language']:
      nl = self.config.get('language', str(authorid))
      if nl in self.langs:
        langs.append(nl)
        if debug: dbg_origins.append('author')
        nl = self.langs[langs[-1]].get('meta', 'inherit', fallback=None)
        while nl and nl not in langs and nl in self.langs:
          langs.append(nl)
          if debug: dbg_origins.append('inherit author')
          nl = self.langs[langs[-1]].get('meta', 'inherit', fallback=None)
    if guildid and str(guildid) in self.config['language']:
      nl = self.config.get('language', str(guildid))
      if nl not in langs and nl in self.langs:
        langs.append(nl)
        if debug: dbg_origins.append('guild')
        nl = self.langs[langs[-1]].get('meta', 'inherit', fallback=None)
        while nl and nl not in langs and nl in self.langs:
          langs.append(nl)
          if debug: dbg_origins.append('inherit guild')
          nl = self.langs[langs[-1]].get('meta', 'inherit', fallback=None)
    
    if self.baselang not in langs:
      langs.append(self.baselang)
      if debug: dbg_origins.append('default')

    if not debug:
      return langs
    else:
      return langs, dbg_origins

  def __call__(self, ctx:commands.Context, scope:str, key:str, **values):
    reqlangs = self.resolve_lang(ctx)

    match = None
    for reqlang in reqlangs:
      if reqlang in self.langs:
        if scope in self.langs[reqlang]:
          if key in self.langs[reqlang][scope]:
            if len(self.langs[reqlang][scope][key]) > 0:
              match = self.langs[reqlang][scope][key]
              break
    
    if match is None:
      return "{MISSING STRING}"
    
    # Fill in values in the string
    for k,v in values.items():
      match = match.replace('{'+k+'}', str(v))
    
    # Fill in conditionals
    conditionalqueries = re.findall(r'{([a-z]*)\?(.*)\|(.*)}', match)
    for conditionalquery in conditionalqueries:
      if conditionalquery[0] in values:
        if values[conditionalquery[0]]:
          replace = conditionalquery[1]
        else:
          replace = conditionalquery[2]
        match=match.replace('{'+conditionalquery[0]+'?'+conditionalquery[1]+'|'+conditionalquery[2]+'}', replace)

    # Fill in config queries
    configqueries = re.findall(r'{c\:([a-z_]*)\/([a-z_]*)}', match)
    for configquery in configqueries:
      if configquery[0] in self.config:
        if configquery[1] in self.config[configquery[0]]:
          match = match.replace('{c:'+configquery[0]+'/'+configquery[1]+'}', self.config[configquery[0]][configquery[1]])

    return match
  
  def list_scope_key_pairs(self, lang):
    pairs = set()
    for scope in self.langs[lang].keys():
      if scope == 'meta': continue
      for key, value in self.langs[lang][scope].items():
        if value:
          pairs.add(f'{scope}/{key}')
    return pairs

  def calculate_coverage(self, langcode:str):
    langvals = self.list_scope_key_pairs(langcode)
    while self.langs[langcode].get('meta', 'inherit', fallback=None):
      langcode = self.langs[langcode].get('meta', 'inherit')
      langvals = langvals.union(self.list_scope_key_pairs(langcode))
    basevals = self.list_scope_key_pairs(self.baselang)

    return int((len(langvals) / max(len(basevals), 1)) * 100)