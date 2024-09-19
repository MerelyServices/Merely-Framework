"""
  Error - Rich error handling cog
  Features: determine the nature of the error and explain what went wrong
  Recommended cogs: Help
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


class Error(commands.Cog):
  """ Catches errors and provides users with a response """
  SCOPE = 'error'

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

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
    print("error detected")
    try:
      if isinstance(error, app_commands.CommandOnCooldown):
        if error.cooldown.get_retry_after() > 5:
          await send(
            self.babel(inter, 'cooldown', t=int(error.cooldown.get_retry_after())),
            ephemeral=True
          )
          return
        print("cooldown")
        return
      kwargs = {'ephemeral': True}
      if isinstance(
        error,
        (app_commands.CommandNotFound, commands.BadArgument, commands.MissingRequiredArgument)
      ):
        if 'Help' in self.bot.cogs:
          await send(
            self.bot.cogs['Help'].resolve_docs(inter, inter.command.name),
            **kwargs
          )
        else:
          await send(self.babel(inter, 'missingrequiredargument'), **kwargs)
        return
      if isinstance(error, app_commands.NoPrivateMessage):
        await send(self.babel(inter, 'noprivatemessage'), **kwargs)
        return
      if isinstance(error, commands.PrivateMessageOnly):
        await send(self.babel(inter, 'privatemessageonly'), **kwargs)
        return
      if isinstance(error, (app_commands.BotMissingPermissions, app_commands.MissingPermissions)):
        permlist = self.bot.babel.string_list(inter, [f'`{p}`' for p in error.missing_permissions])
        me = isinstance(error, app_commands.BotMissingPermissions)
        await send(
          self.babel(inter, 'missingperms', me=me, perms=permlist), **kwargs
        )
        return
      if isinstance(error, app_commands.CommandInvokeError):
        if isinstance(error.original, self.bot.auth.AuthError):
          await send(str(error.original), **kwargs)
          return
        await send(
          self.babel(inter, 'commanderror', error=str(error.original)), **kwargs
        )
        raise error.original
      elif isinstance(error, (app_commands.CheckFailure, commands.CheckAnyFailure)):
        print("Unhandled error;", error)
        return
    except asyncio.TimeoutError:
      print(
        "Unable to handle error in command",
        inter.command.name if inter.command else 'UNKNOWN COMMAND',
        "because the interaction timed out."
      )
      print(error)


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Error(bot))
