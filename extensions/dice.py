"""
  Dice - Random Number Generation
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING
import disnake
from disnake.ext import commands

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

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot

  @commands.slash_command()
  async def dice(self, inter:disnake.CommandInteraction, sides:str = 6):
    """
    Roll an n-sided dice

    Parameters
    ----------
    sides: The number of sides on your dice, separate with commas for multiple dice
    """

    result = []
    for i, n in enumerate(sides.split(',')):
      try:
        result.append(
          self.babel(inter, 'roll_result', i=i+1, r=random.choice(range(1, int(n) + 1)))
        )
      except (ValueError, IndexError):
        return await inter.send(self.babel(inter, 'roll_error'))

    await inter.send('\n'.join(result))


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(Dice(bot))
