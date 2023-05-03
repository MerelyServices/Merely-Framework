"""
  Babel - a translation system for discord bots
  Babel reads and formats strings from language files in the babel folder.
  You can find a language editor at https://github.com/yiays/Babel-Translator
  Recommended cogs: Language
"""

import os, re
from configparser import ConfigParser
from typing import Optional, Union
from disnake import Locale, Guild, Message, Interaction, User, Member
from disnake.ext.commands import Context

class Babel():
  """ Stores language data and resolves and formats it for use in Cogs """
  path = 'babel'
  langs = {}

  def __init__(self, config:ConfigParser):
    self.config = config
    self.conditional = re.compile(r'{([a-z]*?)\?(.*?)\|(.*?)}')
    self.configreference = re.compile(r'{c\:([a-z_]*?)\/([a-z_]*?)}')
    self.prefixreference = re.compile(r'{p\:(local|global)}')
    self.load()

  def load(self):
    """ Load data from config and babel files """
    self.defaultlang = self.config.get('language', 'default', fallback='en')
    # defaultlang is the requested language to default new users to
    self.prefix = self.config.get('language', 'prefix', fallback='')

    if os.path.isfile(self.path):
      os.remove(self.path)
    if (
      not os.path.exists(self.path) or
      not os.path.exists(os.path.join(self.path, self.defaultlang+'.ini'))
    ):
      raise FileNotFoundError(
        f"The path {self.path} must exist and contain a complete {self.defaultlang}.ini."
      )

    for langfile in os.scandir(self.path):
      langfile = langfile.name
      if langfile[-4:] == '.ini':
        langname = langfile[:-4]
        self.langs[langname] = ConfigParser(comment_prefixes='@', allow_no_value=True)
        # create a configparser that should preserve comments
        self.langs[langname].read(os.path.join(self.path, langfile), encoding='utf-8')
        if 'meta' not in self.langs[langname]:
          self.langs[langname].add_section('meta')
        self.langs[langname].set('meta', 'language', langname)
        with open(os.path.join(self.path, langfile), 'w', encoding='utf-8') as file:
          self.langs[langname].write(file)

    # baselang is the root language file that should be considered the most complete.
    self.baselang = self.defaultlang
    while self.langs[self.baselang].get('meta', 'inherit', fallback=''):
      newbaselang = self.langs[self.baselang].get('meta', 'inherit')
      if newbaselang in self.langs:
        self.baselang = newbaselang
      else:
        print("WARNING: unable to resolve language dependancy chain.")

  def reload(self):
    """ Reset data and load again """
    self.langs = {}
    self.load()

  def localeconv(self, locale:Locale) -> str:
    """ Converts a Discord API locale to a babel locale """
    return self.prefix + str(locale).replace('-US', '').replace('-UK', '')

  def resolve_lang(
    self,
    user:Optional[User] = None,
    guild:Optional[Guild] = None,
    inter:Optional[Interaction] = None,
    debug=False
  ) -> tuple[list]:
    """ Creates a priority list of languages and reasons why they apply to this user or guild """
    langs = []
    dbg_origins = []

    def resolv(locale, origin):
      """ Find the specific babel lang struct for this locale """
      if locale not in self.langs and '_' in locale:
        # Guess that the non-superset version of the language is what it would've inherited from
        locale = locale.split('_')[0]
      if locale in self.langs:
        # A language file was found
        langs.append(locale)
        if debug:
          dbg_origins.append(origin)
        # Follow the inheritance chain
        locale = self.langs[langs[-1]].get('meta', 'inherit', fallback=None)
        # Loop interrupts if this chain has been followed before
        while locale and locale not in langs and locale in self.langs:
          langs.append(locale)
          if debug:
            dbg_origins.append('inherit '+origin)
          locale = self.langs[langs[-1]].get('meta', 'inherit', fallback=None)

    # Manually set language for user
    if user and str(user.id) in self.config['language']:
      locale = self.config.get('language', str(user.id))
      resolv(locale, 'author')
    # User locale
    if inter:
      locale = self.localeconv(inter.locale)
      resolv(locale, 'author_locale')
    # Manually set language for guild
    if guild and str(guild.id) in self.config['language']:
      locale = self.config.get('language', str(guild.id))
      resolv(locale, 'guild')
    # Guild locale (if it has been set manually)
    if inter and inter.guild and 'COMMUNITY' in inter.guild.features:
      locale = self.localeconv(inter.guild_locale)
      resolv(locale, 'guild_locale')
    # Default language
    if self.defaultlang not in langs:
      resolv(self.defaultlang, 'default')

    if not debug:
      return langs
    return langs, dbg_origins

  def __call__(
    self,
    target:Union[Context, Interaction, Message, User, Member, Guild, tuple],
    scope:str,
    key:str,
    **values
  ):
    """ Determine the locale and resolve the closest translated string """
    inter = None
    if isinstance(target, (Context, Interaction, Message)):
      author = target.author
      guild = target.guild if hasattr(target, 'guild') and target.guild else None
      if isinstance(target, Interaction):
        inter = target
    elif isinstance(target, User):
      author = target
      guild = None
    elif isinstance(target, Member):
      author = target
      guild = target.guild
    elif isinstance(target, Guild):
      author = None
      guild = target
    else:
      author = target[0]
      guild = target[1] if len(target)>1 else None

    reqlangs = self.resolve_lang(author, guild, inter)

    match: Optional[str] = None
    for reqlang in reqlangs:
      try:
        match = self.langs[reqlang][scope][key]
        break
      except (ValueError, KeyError):
        continue

    if match is None:
      return "{MISSING STRING}"

    # Fill in values in the string
    for key,value in values.items():
      match = match.replace('{'+key+'}', str(value))

    # Fill in prefixes
    prefixqueries = self.prefixreference.findall(match)
    for prefixquery in prefixqueries:
      if prefixquery == 'local' and guild:
        match = match.replace(
          '{p:'+prefixquery+'}',
          self.config.get('prefix', str(guild.id), fallback=self.config['main']['prefix_short'])
        )
      else:
        match = match.replace('{p:'+prefixquery+'}', self.config['main']['prefix_short'])

    # Fill in conditionals
    conditionalqueries = self.conditional.findall(match)
    for conditionalquery in conditionalqueries:
      if conditionalquery[0] in values:
        if values[conditionalquery[0]]:
          replace = conditionalquery[1]
        else:
          replace = conditionalquery[2]
        match=match.replace(
          '{'+conditionalquery[0]+'?'+conditionalquery[1]+'|'+conditionalquery[2]+'}',
          replace
        )

    # Fill in config queries
    configqueries = self.configreference.findall(match)
    for configquery in configqueries:
      if configquery[0] in self.config:
        if configquery[1] in self.config[configquery[0]]:
          match = match.replace(
            '{c:'+configquery[0]+'/'+configquery[1]+'}',
            self.config[configquery[0]][configquery[1]]
          )
    
    # Handle \n
    match = match.replace('\\n', '\n')

    return match

  def list_scope_key_pairs(self, lang):
    """ Breaks down the structure of a babel file for evaluation """
    pairs = set()
    inheritlang = lang
    while inheritlang and inheritlang in self.langs:
      for scope in self.langs[inheritlang].keys():
        if scope == 'meta':
          continue
        for key, value in self.langs[inheritlang][scope].items():
          if value:
            pairs.add(f'{scope}/{key}')
      inheritlang = self.langs[inheritlang].get('meta', 'inherit', fallback='')
    return pairs

  def calculate_coverage(self, lang:str):
    """ Compares the number of strings between a language and the baselang """
    langvals = self.list_scope_key_pairs(lang)
    basevals = self.list_scope_key_pairs(self.defaultlang) #TODO: don't run this every time.

    return int((len(langvals) / max(len(basevals), 1)) * 100)
