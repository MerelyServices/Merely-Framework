"""
  Error Test - A test module for the error module, makes it easy to ensure error handling is working
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
  from main import MerelyBot


class ErrorTest(commands.Cog):
  """ Adds an echo command and logs new members """
  def __init__(self, bot:MerelyBot):
    self.bot = bot

    self.throw_error_ctx_user = app_commands.ContextMenu(
      name='Throw Error',
      allowed_contexts=app_commands.AppCommandContext(guild=True, private_channel=True),
      allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
      callback=self.throw_error_ctx_user_callback
    )
    bot.tree.add_command(self.throw_error_ctx_user)

    self.throw_error_ctx_msg = app_commands.ContextMenu(
      name='Throw Error',
      allowed_contexts=app_commands.AppCommandContext(guild=True, private_channel=True),
      allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
      callback=self.throw_error_ctx_msg_callback
    )
    bot.tree.add_command(self.throw_error_ctx_msg)

  async def cog_unload(self) -> None:
    self.bot.tree.remove_command(self.throw_error_ctx_user.name, type=discord.AppCommandType.user)
    self.bot.tree.remove_command(self.throw_error_ctx_msg.name, type=discord.AppCommandType.message)

  async def throw_error_ctx_user_callback(self, _:discord.Interaction, _1:discord.User):
    """ Throws an error for testing """
    raise Exception("Command failed successfully")

  async def throw_error_ctx_msg_callback(self, _:discord.Interaction, _1:discord.Message):
    """ Throws an error for testing """
    raise Exception("Command failed successfully")

  @app_commands.command()
  @app_commands.allowed_contexts(guilds=True, private_channels=True)
  @app_commands.allowed_installs(guilds=True, users=True)
  async def throw_error(self, _:discord.Interaction):
    """ Throws an error for testing """
    raise Exception("Command failed successfully")


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(ErrorTest(bot))
