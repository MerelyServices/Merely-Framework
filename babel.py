"""
  Babel - a translation system for discord bots
  Babel reads and formats strings from language files in the babel folder.
  You can find a language editor at https://github.com/yiays/Babel-Translator
  Recommended cogs: Language
"""
from __future__ import annotations

import os, re
from configparser import ConfigParser
from typing import Optional, TYPE_CHECKING
from config import Config
from glob import glob
import discord
from discord import app_commands

if TYPE_CHECKING:
  from .main import MerelyBot

Resolvable = (
  discord.Interaction | discord.Message | discord.User | discord.Member | discord.Guild
  | tuple[int, int | None]
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

  # App command data - for mentioning
  appcommands: list[app_commands.AppCommand]

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
    self.filter_commandreference = re.compile(r'{p\:([a-z_ -]*?)}')
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
        print("WARN: unable to resolve language dependancy chain.")

  async def cache_appcommands(self, bot:MerelyBot):
    self.appcommands = await bot.tree.fetch_commands()

  def localeconv(self, locale:discord.Locale) -> str:
    """ Converts a Discord API locale to a babel locale """
    return self.prefix + str(locale).replace('-US', '').replace('-UK', '')

  def resolve_lang(
    self,
    user_id:Optional[int] = None,
    guild_id:Optional[int] = None,
    inter:Optional[discord.Interaction] = None,
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
    fallback:str | None = None,
    **values: dict[str, str | bool]
  ) -> str:
    """ Determine the locale and resolve the closest translated string """
    inter = None
    if isinstance(target, discord.Interaction):
      author_id = target.user.id
      guild_id = target.guild.id if target.guild else None
      inter = target
    elif isinstance(target, discord.Message):
      author_id = target.author.id
      guild_id = target.guild.id if target.guild else None
    elif isinstance(target, discord.User):
      author_id = target.id
      guild_id = None
    elif isinstance(target, discord.Member):
      author_id = target.id
      guild_id = target.guild.id
    elif isinstance(target, discord.Guild):
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
      if fallback:
        match = fallback
      else:
        variables = self.string_list(target, [k+'={'+k+'}' for k in values])
        match = "{" + key.upper() + (': '+variables if variables else '') + "}"

    # Fill in variables in the string
    for varname,varval in values.items():
      match = match.replace('{'+varname+'}', str(varval))

    # Fill in command queries
    commandqueries = self.filter_commandreference.findall(match)
    for commandquery in commandqueries:
      match = match.replace(
        '{p:'+commandquery+'}',
        self.mention_command(commandquery)
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

  def mention_command(self, command_name:str):
    """ Finds the API slash command and mentions it """
    mentionables = [a for a in self.appcommands if a.name == command_name]
    if mentionables:
      #TODO: the first match might not always be the right one...
      return mentionables[0].mention
    else:
      return '/'+command_name

  def string_list(self, target:Resolvable, items:list[str], or_mode:bool = False) -> str:
    """ Takes list items, and joins them together in a regionally correct way """
    CONJUNCTION = (
      self(target, 'main', 'list_conjunction', fallback=', ').replace('_', ' ')
    )
    if or_mode:
      CONJUNCTION_2 = (
        self(target, 'main', 'list_conjunction_2_or', fallback=' or ').replace('_', ' ')
      )
      CONJUNCTIONLAST = (
        self(target, 'main', 'list_last_conjunction_or', fallback=', or ').replace('_', ' ')
      )
    else:
      CONJUNCTION_2 = (
        self(target, 'main', 'list_conjunction_2', fallback=' and ').replace('_', ' ')
      )
      CONJUNCTIONLAST = (
        self(target, 'main', 'list_last_conjunction', fallback=', and ').replace('_', ' ')
      )

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

  def scope_key_pairs(self, lang) -> set[str]:
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
    langvals = self.scope_key_pairs(lang)
    basevals = self.scope_key_pairs(self.defaultlang)

    return int((len(langvals) / max(len(basevals), 1)) * 100)
