"""
  Language - Internationalisation features powered by Babel
  Features: Rich translation, online editor
  Related: https://github.com/yiays/Babel-Translator
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import re
import discord
from discord import app_commands
from discord.ext import commands

from extensions.controlpanel import Selectable

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


class Language(commands.Cog):
  """ Enables per-user and per-guild string translation of the bot """
  SCOPE = 'language'

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    # ensure config file has required data
    # There are more keys which are handled in config.py
    # This is because they need to exist before the bot can start
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)
    if 'show_in_controlpanel' not in self.config:
      self.config['show_in_controlpanel'] = 'True'

  def controlpanel_settings(self, inter:discord.Interaction):
    # ControlPanel integration
    langlist = list(self.bot.babel.langs.keys())
    if not self.config.getboolean('show_in_controlpanel', fallback=True):
      return []
    out = [Selectable(
      self.SCOPE,
      str(inter.user.id),
      'user_language_override',
      [discord.SelectOption(label=val) for val in langlist]
    )]
    if inter.guild and inter.permissions.administrator:
      out.append(Selectable(
        self.SCOPE,
        str(inter.guild_id),
        'guild_language_override',
        [discord.SelectOption(label=val) for val in langlist]
      ))
    return out

  language = app_commands.Group(
    name='language',
    description="Changes the language this bot speaks to you, or to a server you administrate"
  )

  @language.command(name='list')
  async def language_list(self, inter:discord.Interaction):
    """
    Lists all available languages this bot can be translated to
    """
    embed = discord.Embed(
      title=self.babel(inter, 'list_title'),
      description=self.babel(inter, 'set_howto') +
      '\n' + (
        self.babel(inter, 'contribute_cta') if self.config['contribute_url'] else ''
      ),
      color=int(self.bot.config['main']['themecolor'], 16)
    )

    for langcode,language in self.bot.babel.langs.items():
      if prefix := self.config['prefix']:
        if not langcode.startswith(prefix):
          continue
      coverage = self.bot.babel.calculate_coverage(langcode)
      embed.add_field(
        name=language.get('meta', 'name') + ' (' + langcode.replace(prefix, '') + ')',
        value=language.get(
          'meta',
          'contributors',
          fallback=self.babel(inter, 'unknown_contributors')
        ) + '\n' +
        self.babel(inter, 'coverage_label', coverage=coverage) + '\n' +
        self.bot.utilities.progress_bar(coverage, 100) + '\n',
        inline=False
      )

    await inter.response.send_message(embed=embed)

  @language.command(name='get')
  async def language_get(self, inter:discord.Interaction):
    """
    Get the language the bot is using with you right now and the reason why it was selected
    """
    langs, origins = self.bot.babel.resolve_lang(
      user_id=inter.user.id,
      guild_id=inter.guild.id if inter.guild else None,
      inter=inter,
      debug=True
    )

    embeds = []
    backup = False
    for lang, origin in zip(langs, origins):
      if origin.startswith('inherit'):
        origin = 'inherit'
      #BABEL: -origin_reason_,origin_reason_author,origin_reason_guild,origin_reason_default
      #BABEL: origin_reason_author_locale,origin_reason_guild_locale,origin_reason_inherit
      embeds.append(discord.Embed(
        title=f"{self.bot.babel.langs[lang].get('meta', 'name')} ({lang})",
        description=self.babel(inter, 'origin_reason_'+origin, backup=backup),
        color=int(self.bot.config['main']['themecolor'], 16)
      ))
      backup = True

    await inter.response.send_message(embeds=embeds)

  @language.command(name='set')
  @app_commands.describe(language="An ISO language code for your language and dialect")
  async def language_set(
    self,
    inter:discord.Interaction,
    language:str
  ):
    """
      Change the language that this bot uses with you or a server you manage
    """
    if not language == 'default' and re.match(r'[a-z]{2}(-[A-Z]{2})?$', language) is None:
      await inter.response.send_message(self.babel(inter, 'set_failed_invalid_pattern'))
    else:
      prefix = self.config.get('prefix', fallback='')
      if language != 'default':
        if not language.startswith(prefix):
          language = prefix + language
      if (
        isinstance(inter.user, discord.User) or
        not inter.user.guild_permissions.administrator
      ):
        usermode = True
        if language == 'default':
          self.config.pop(str(inter.user.id))
        else:
          self.config[str(inter.user.id)] = language
      else:
        usermode = False
        if language == 'default':
          self.config.pop(str(inter.guild.id))
        else:
          self.config[str(inter.guild.id)] = language
      self.bot.config.save()
      if language == 'default' or language in self.bot.babel.langs.keys():
        #BABEL: set_success,unset_success
        await inter.response.send_message(self.babel(
          inter,
          'unset_success' if language == 'default' else 'set_success',
          language=(
            self.bot.babel.langs[self.bot.babel.defaultlang].get('meta', 'name')
            if language == 'default' else
            self.bot.babel.langs[language].get('meta', 'name')
          ),
          usermode=usermode)
        )
      else:
        await inter.response.send_message(
          self.babel(inter, 'set_warning_no_match')+'\n' +
          self.babel(inter, 'contribute_cta')
        )

  @language_set.autocomplete('language')
  async def language_set_ac(self, _:discord.Interaction, search:str):
    """ Suggests languages that are already available """
    matches = []
    prefix = self.config['prefix']
    for lang in self.bot.babel.langs.keys():
      if lang.startswith(prefix) and search in lang:
        langname = lang.replace(prefix, '')
        matches.append(app_commands.Choice(name=langname, value=lang))
    if len(matches) > 25:
      matches = matches[:24] + [app_commands.Choice(name='...', value='')]
    if 'default'.startswith(search):
      matches.insert(0, app_commands.Choice(name='default', value='default'))
    return matches


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Language(bot))
