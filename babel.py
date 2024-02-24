"""
  Babel - a translation system for discord bots
  Babel reads and formats strings from language files in the babel folder.
  You can find a language editor at https://github.com/yiays/Babel-Translator
  Recommended cogs: Language
"""

import os, re
from configparser import ConfigParser
from typing import Optional
from config import Config
from glob import glob
import disnake
from disnake.ext import commands

Resolvable = (
  commands.Context | disnake.Interaction | disnake.Message | disnake.User | disnake.Member
  | disnake.Guild | tuple
)


class Babel():
  """ Stores language data and resolves and formats it for use in Cogs """
  path:str
  backup_path:Optional[str] = None
  config: Config
  langs: dict[str, ConfigParser]
  scope_key_cache: dict

  # Regex patterns
  filter_conditional: re.Pattern
  filter_configreference: re.Pattern
  filter_commandreference: re.Pattern

  @property
  def defaultlang(self) -> str:
    """ The default language which should have all strings """
    return self.config.get('language', 'default', fallback='en')

  @property
  def prefix(self) -> str:
    """ The default bot prefix """
    return self.config.get('language', 'prefix', fallback='')

  def __init__(self, config:Config, path='babel'):
    """ Called once on import """
    self.path = path
    if path != 'babel':
      self.backup_path = 'babel'
    self.config = config
    self.filter_conditional = re.compile(r'{([a-z]*?)\?(.*?)\|(.*?)}')
    self.filter_configreference = re.compile(r'{c\:([a-z_]*?)\/([a-z_]*?)}')
    self.filter_commandreference = re.compile(r'{p\:([a-z_ ]*?)}')
    self.load()

  def load(self):
    """ Load data from config and babel files, called upon reload """
    # Reset cache
    self.langs = {}
    self.scope_key_cache = {}

    if (
      (
        not os.path.exists(self.path) or
        not os.path.exists(os.path.join(self.path, self.defaultlang+'.ini'))
      ) and
      (self.backup_path and (
        not os.path.exists(self.backup_path) or
        not os.path.exists(os.path.join(self.backup_path, self.defaultlang+'.ini'))
      ))
    ):
      raise FileNotFoundError(
        f"The path {self.path} must exist and contain a complete {self.defaultlang}.ini."
      )

    for langpath in (glob(self.path + os.path.sep + '*.ini') +
                     (glob(self.backup_path + os.path.sep + '*.ini') if self.backup_path else [])):
      langfile = re.sub(r'^(babel[/\\]|overlay[/\\]babel[/\\])', '', langpath)
      langname = langfile[:-4]
      self.langs[langname] = ConfigParser(comment_prefixes='@', allow_no_value=True)
      # create a Config that should preserve comments
      self.langs[langname].read(langpath, encoding='utf-8')

    # baselang is the root language file that should be considered the most complete.
    self.baselang = self.defaultlang
    while self.langs[self.baselang].get('meta', 'inherit', fallback=''):
      newbaselang = self.langs[self.baselang].get('meta', 'inherit')
      if newbaselang in self.langs:
        self.baselang = newbaselang
      else:
        print("WARNING: unable to resolve language dependancy chain.")

  def localeconv(self, locale:disnake.Locale) -> str:
    """ Converts a Discord API locale to a babel locale """
    return self.prefix + str(locale).replace('-US', '').replace('-UK', '')

  def resolve_lang(
    self,
    user_id:Optional[int] = None,
    guild_id:Optional[int] = None,
    inter:Optional[disnake.Interaction] = None,
    debug:bool = False
  ) -> tuple[list]:
    """ Creates a priority list of languages and reasons why they apply to this user or guild """
    langs = []
    dbg_origins = []

    def resolv(locale:str, origin:str):
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
    if user_id and str(user_id) in self.config['language']:
      locale = self.config.get('language', str(user_id))
      resolv(locale, 'author')
    # User locale
    if inter:
      locale = self.localeconv(inter.locale)
      resolv(locale, 'author_locale')
    # Manually set language for guild
    if guild_id and str(guild_id) in self.config['language']:
      locale = self.config.get('language', str(guild_id))
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
    target:Resolvable,
    scope:str,
    key:str,
    **values: dict[str, str | bool]
  ) -> str:
    """ Determine the locale and resolve the closest translated string """
    inter = None
    if isinstance(target, (commands.Context, disnake.Interaction, disnake.Message)):
      author_id = target.author.id
      guild_id = target.guild.id if hasattr(target, 'guild') and target.guild else None
      if isinstance(target, disnake.Interaction):
        inter = target
    elif isinstance(target, disnake.User):
      author_id = target.id
      guild_id = None
    elif isinstance(target, disnake.Member):
      author_id = target.id
      guild_id = target.guild.id
    elif isinstance(target, disnake.Guild):
      author_id = None
      guild_id = target.id
    else:
      author_id = target[0]
      guild_id = target[1] if len(target) > 1 else None

    reqlangs = self.resolve_lang(author_id, guild_id, inter)

    match: Optional[str] = None
    for reqlang in reqlangs:
      try:
        match = self.langs[reqlang][scope][key]
        break
      except (ValueError, KeyError):
        continue

    if match is None:
      # Placeholder string when no strings are found
      variables = self.string_list(target, [k+'={'+k+'}' for k in values])
      match = "{" + key.upper() + (': '+variables if variables else '') + "}"

    # Fill in variables in the string
    for varname,varval in values.items():
      match = match.replace('{'+varname+'}', str(varval))

    # Fill in command queries
    commandqueries = self.filter_commandreference.findall(match)
    for commandquery in commandqueries:
      # Prefixes are simplified if message commands are disabled
      if not self.config.getboolean('intents', 'message_content'):
        if hasattr(target, 'bot'):
          cmd = target.bot.get_global_command_named(commandquery)
          if isinstance(cmd, disnake.APISlashCommand):
            match = match.replace('{p:'+commandquery+'}', '</'+cmd.name+':'+str(cmd.id)+'>')
        match = match.replace('{p:'+commandquery+'}', '/'+commandquery)
      elif guild_id:
        guildprefix = self.config.get(
          'prefix', str(guild_id), fallback=self.config['main']['prefix_short']
        )
        match = match.replace(
          '{p:'+commandquery+'}',
          guildprefix + commandquery
        )
      else:
        match = match.replace(
          '{p:'+commandquery+'}', self.config['main']['prefix_short'] + commandquery
        )

    # Fill in conditionals
    conditionalqueries = self.filter_conditional.findall(match)
    for conditionalquery in conditionalqueries:
      if conditionalquery[0] in values:
        if values[conditionalquery[0]]:
          replace = conditionalquery[1]
        else:
          replace = conditionalquery[2]
        match = match.replace(
          '{'+conditionalquery[0]+'?'+conditionalquery[1]+'|'+conditionalquery[2]+'}',
          replace
        )

    # Fill in config queries
    configqueries = self.filter_configreference.findall(match)
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

  def string_list(self, target:Resolvable, items:list[str], or_mode:bool = False) -> str:
    """ Takes list items, and joins them together in a regionally correct way """
    CONJUNCTION = self(target, 'main', 'list_conjunction').replace('_', ' ')
    if or_mode:
      CONJUNCTION_2 = self(target, 'main', 'list_conjunction_2_or').replace('_', ' ')
      CONJUNCTIONLAST = self(target, 'main', 'list_last_conjunction_or').replace('_', ' ')
    else:
      CONJUNCTION_2 = self(target, 'main', 'list_conjunction_2').replace('_', ' ')
      CONJUNCTIONLAST = self(target, 'main', 'list_last_conjunction').replace('_', ' ')

    items = list(items)
    if len(items) > 2:
      i = 0
      for i in range(len(items) - 2):
        items.insert(i * 2 + 1, CONJUNCTION)
      i += 1
      items.insert(i * 2 + 1, CONJUNCTIONLAST)
    elif len(items) > 1:
      items.insert(1, CONJUNCTION_2)

    return ''.join(items)

  def list_scope_key_pairs(self, lang) -> set[str]:
    """ Breaks down the structure of a babel file for evaluation """
    # Check cache first
    if lang in self.scope_key_cache:
      return self.scope_key_cache[lang]

    # List all scope key pairs in this language and any it inherits from
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

    # Store result in cache
    self.scope_key_cache[lang] = pairs
    return pairs

  def calculate_coverage(self, lang:str) -> int:
    """ Compares the number of strings between a language and the baselang """
    langvals = self.list_scope_key_pairs(lang)
    basevals = self.list_scope_key_pairs(self.defaultlang)

    return int((len(langvals) / max(len(basevals), 1)) * 100)
