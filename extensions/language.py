"""
  Language - Internationalisation features powered by Babel
  Features: Rich translation, online editor
  Related: https://github.com/yiays/Babel-Translator
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import re
import disnake
from disnake.ext import commands

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

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)

  def controlpanel_settings(self, inter:disnake.Interaction):
    # ControlPanel integration
    langlist = list(self.bot.babel.langs.keys())
    out = [
      Selectable(self.SCOPE, str(inter.user.id), 'user_language_override', langlist)
    ]
    if inter.guild and inter.permissions.administrator:
      out.append(Selectable(self.SCOPE, str(inter.guild_id), 'guild_language_override', langlist))
    return out

  @commands.slash_command()
  async def language(self, _:disnake.CommandInteraction):
    """
    Changes the language this bot speaks to you, or to a server you administrate
    """

  @language.sub_command(name='list')
  async def language_list(self, inter:disnake.CommandInteraction):
    """
    Lists all available languages this bot can be translated to
    """
    embed = disnake.Embed(
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

    await inter.send(embed=embed)

  @language.sub_command(name='get')
  async def language_get(self, inter:disnake.CommandInteraction):
    """
    Get the language the bot is using with you right now and the reason why it was selected
    """
    langs, origins = self.bot.babel.resolve_lang(
      user_id=inter.author.id,
      guild_id=inter.guild.id,
      inter=inter,
      debug=True
    )

    embeds = []
    backup = False
    for lang, origin in zip(langs, origins):
      if origin.startswith('inherit'):
        origin = 'inherit'
      embeds.append(disnake.Embed(
        title=f"{self.bot.babel.langs[lang].get('meta', 'name')} ({lang})",
        description=self.babel(inter, 'origin_reason_'+origin, backup=backup),
        color=int(self.bot.config['main']['themecolor'], 16)
      ))
      backup = True

    await inter.send(embeds=embeds)

  @language.sub_command(name='set')
  async def language_set(
    self,
    inter:disnake.CommandInteraction,
    language:str
  ):
    """
    Change the language that this bot uses with you or a server you manage

    Parameters
    ----------
    language: An ISO language code for your language and dialect
    """
    if not language == 'default' and re.match(r'[a-z]{2}(-[A-Z]{2})?$', language) is None:
      await inter.send(self.babel(inter, 'set_failed_invalid_pattern'))
    else:
      if language != 'default':
        language = self.config.get('prefix', fallback='')+language
      if (
        isinstance(inter.author, disnake.User) or
        not inter.author.guild_permissions.administrator
      ):
        usermode = True
        if language == 'default':
          self.bot.config.remove_option(self.SCOPE, str(inter.author.id))
        else:
          self.config[str(inter.author.id)] = language
      else:
        usermode = False
        if language == 'default':
          self.bot.config.remove_option(self.SCOPE, str(inter.guild.id))
        else:
          self.config[str(inter.guild.id)] = language
      self.bot.config.save()
      if language == 'default' or language in self.bot.babel.langs.keys():
        await inter.send(self.babel(
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
        await inter.send(
          self.babel(inter, 'set_warning_no_match')+'\n' +
          self.babel(inter, 'contribute_cta')
        )

  @language_set.autocomplete('language')
  def language_set_ac(self, _:disnake.MessageCommandInteraction, search:str):
    """ Suggests languages that are already available """
    matches = []
    prefix = self.config['prefix']
    for lang in self.bot.babel.langs.keys():
      if lang.startswith(prefix) and search in lang:
        matches.append(lang.replace(prefix, ''))
    if len(matches) > 24:
      matches = matches[:23] + ['...']
    return (['default'] if 'default'.startswith(search) else []) + matches


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(Language(bot))
