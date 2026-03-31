"""
  Error - Rich error handling cog
  Features: determine the nature of the error and explain what went wrong
  Recommended cogs: Help
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from main import MerelyCog

if TYPE_CHECKING:
  from main import MerelyBot
  from extensions.help import Help


class Error(MerelyCog):
  """ Catches errors and provides users with a response """
  SCOPE = 'error'

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    bot.tree.error(self.handle_error)

  async def handle_error(
    self,
    inter:discord.Interaction,
    error:app_commands.AppCommandError
  ):
    """ Report to the user what went wrong """
    send = (inter.followup.send if inter.response.is_done() else inter.response.send_message)
    realerror: Exception = error
    if isinstance(error, app_commands.CommandInvokeError):
      if isinstance(error.original, self.bot.auth.AuthError):
        await send(str(error.original))
        return
      realerror = error.original
    print("error detected")
    try:
      if isinstance(realerror, app_commands.CommandOnCooldown):
        if realerror.cooldown.get_retry_after() > 5:
          await send(
            self.babel(inter, 'cooldown', t=str(int(realerror.cooldown.get_retry_after()))),
            ephemeral=True
          )
          return
        print("cooldown")
        return
      if isinstance(
        error,
        (app_commands.CommandNotFound, commands.BadArgument, commands.MissingRequiredArgument)
      ):
        if 'Help' in self.bot.cogs:
          help = cast("Help", self.bot.cogs['Help'])
          assert inter.command is not None
          await send(
            content=await help.resolve_docs(inter, inter.command.name),
            ephemeral=True
          )
        else:
          await send(self.babel(inter, 'missingrequiredargument'), ephemeral=True)
        return
      if isinstance(error, app_commands.NoPrivateMessage):
        await send(self.babel(inter, 'noprivatemessage'), ephemeral=True)
        return
      if isinstance(error, commands.PrivateMessageOnly):
        await send(self.babel(inter, 'privatemessageonly'), ephemeral=True)
        return
      if isinstance(error, (app_commands.BotMissingPermissions, app_commands.MissingPermissions)):
        permlist = self.bot.babel.string_list(inter, [f'`{p}`' for p in error.missing_permissions])
        me = isinstance(error, app_commands.BotMissingPermissions)
        await send(
          self.babel(inter, 'missingperms', me=me, perms=permlist), ephemeral=True
        )
        return
      if isinstance(error, (app_commands.CheckFailure, commands.CheckAnyFailure)):
        print("Unhandled error;", error)
        return
      print("Unknown error;", error)
      raise error
    except asyncio.TimeoutError:
      print(
        "Unable to handle error in command",
        inter.command.name if inter.command else 'UNKNOWN COMMAND',
        "because the interaction timed out."
      )
      print(error)
    except Exception as e:
      raise e from error


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Error(bot))
