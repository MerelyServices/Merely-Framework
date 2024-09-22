"""
  Dice - Random Number Generation
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


class Dice(commands.Cog):
  """ Rolls dice and shares the result """
  SCOPE = 'dice'

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot

  @app_commands.command()
  @app_commands.describe(
    sides="The number of sides on your dice, separate with commas for multiple dice"
  )
  @app_commands.default_permissions(send_messages=True)
  @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
  @app_commands.allowed_installs(guilds=True, users=True)
  async def dice(self, inter:discord.Interaction, sides:str = '6'):
    """
    Roll an n-sided dice
    """

    result = []
    for i, n in enumerate(sides.split(',')):
      try:
        result.append(
          self.babel(inter, 'roll_result', i=i+1, r=random.choice(range(1, int(n) + 1)))
        )
      except (ValueError, IndexError):
        return await inter.response.send_message(self.babel(inter, 'roll_error'))

    await inter.response.send_message('\n'.join(result))


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Dice(bot))
