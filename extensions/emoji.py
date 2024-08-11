"""
  Emoji - Nitro-like emoji features for all users
  Allows users to use emoji from other servers by command
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import disnake
from disnake.ext import commands

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


class Emoji(commands.Cog):
  """ Emojis from guilds as commands """
  SCOPE = 'emoji'

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot

  @commands.slash_command()
  async def emoji(self, inter:disnake.CommandInteraction, search:str):
    """
    Searches emojis from all servers merely is a part of for one to use

    Parameters
    ----------
    search: Type to refine your search
    """
    emojiname = search.split(' ', maxsplit=1)[0].replace(':','').lower()

    if '(' in search:
      try:
        guild = self.bot.get_guild(int(search.split('(')[1][:-1]))
      except ValueError:
        matches = []
      else:
        matches = [e for e in guild.emojis if emojiname == e.name.lower()] if guild else []
    else:
      matches = [e for e in self.bot.emojis if emojiname == e.name.lower()]

    if matches:
      await inter.send(matches[0])
    else:
      await inter.send(self.babel(inter, 'not_found'))

  @emoji.autocomplete('search')
  def ac_emoji(self, _:disnake.CommandInteraction, search:str):
    """ Autocomplete for emoji search """
    results = [
      f':{e.name}: ({e.guild_id})'
      for e in self.bot.emojis if search.replace(':','').lower() in e.name.lower()
    ]
    return results[:25]


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(Emoji(bot))
