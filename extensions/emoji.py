"""
  Emoji - Nitro-like emoji features for all users
  Allows users to use emoji from other servers by command
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import discord
from discord import app_commands

from main import MerelyCog

if TYPE_CHECKING:
  from main import MerelyBot


class Emoji(MerelyCog):
  """ Emojis from guilds as commands """
  SCOPE = 'emoji'

  def __init__(self, bot:MerelyBot):
    self.bot = bot

  @app_commands.command(
    name=app_commands.locale_str('emoji', scope=SCOPE),
    description=app_commands.locale_str('emoji_desc', scope=SCOPE),
  )
  @app_commands.describe(search=app_commands.locale_str('emoji_search_desc', scope=SCOPE))
  @app_commands.allowed_contexts(guilds=True)
  async def emoji(self, inter:discord.Interaction, search:str):
    """
    Searches emojis from all servers merely is a part of for one to use
    """
    emojiname = search.split(' ', maxsplit=1)[0].replace(':','').lower()

    if search.isdigit():
      matches = [e for e in self.bot.emojis if e.id == int(search)]
    else:
      matches = [e for e in self.bot.emojis if emojiname == e.name.lower()]

    if matches:
      await inter.response.send_message(matches[0])
    else:
      await inter.response.send_message(self.babel(inter, 'not_found'))

  @emoji.autocomplete('search')
  async def ac_emoji(self, _:discord.Interaction, search:str):
    """ Autocomplete for emoji search """
    results = [
      app_commands.Choice(name=f':{e.name}: ({getattr(e.guild, 'name', '')})', value=str(e.id))
      for e in self.bot.emojis
      if search.replace(':','').lower() in e.name.lower() + getattr(e.guild, 'name', '')
    ]
    return results[:25]


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Emoji(bot))
