"""
  Error Test - A test module for the error module, makes it easy to ensure error handling is working
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from disnake.ext import commands

if TYPE_CHECKING:
  from main import MerelyBot


class ErrorTest(commands.Cog):
  """ Adds an echo command and logs new members """
  def __init__(self, bot:MerelyBot):
    self.bot = bot

  @commands.user_command(name='throw_error')
  async def throw_error_usr(self, _):
    """ Throws an error for testing """
    raise Exception("Command failed successfully")

  @commands.message_command(name='throw_error')
  async def throw_error_msg(self, _):
    """ Throws an error for testing """
    raise Exception("Command failed successfully")

  @app_commands.command(name='throw_error')
  async def throw_error_slash(self, _):
    """ Throws an error for testing """
    raise Exception("Command failed successfully")


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(ErrorTest(bot))
