"""
  Error - Rich error handling cog
  Features: determine the nature of the error and explain what went wrong
  Recommended cogs: Help
"""

from __future__ import annotations

from typing import TYPE_CHECKING
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

  @commands.Cog.listener('on_user_command_error')
  @commands.Cog.listener('on_message_command_error')
  @commands.Cog.listener('on_slash_command_error')
  async def handle_error(
    self,
    inter:disnake.Interaction,
    error:commands.CommandError
  ):
    """ Report to the user what went wrong """
    print("error detected")
    try:
      if isinstance(error, commands.CommandOnCooldown):
        if error.cooldown.get_retry_after() > 5:
          await inter.response.send_message(
            self.babel(inter, 'cooldown', t=int(error.cooldown.get_retry_after())),
            ephemeral=True
          )
          return
        print("cooldown")
        return
      kwargs = {'ephemeral': True}
      if isinstance(
        error,
        (commands.CommandNotFound, commands.BadArgument, commands.MissingRequiredArgument)
      ):
        if 'Help' in self.bot.cogs:
          await self.bot.cogs['Help'].help(inter, inter.application_command.name, **kwargs)
        else:
          await inter.response.send_message(self.babel(inter, 'missingrequiredargument'), **kwargs)
        return
      if isinstance(error, commands.NoPrivateMessage):
        await inter.response.send_message(self.babel(inter, 'noprivatemessage'), **kwargs)
        return
      if isinstance(error, commands.PrivateMessageOnly):
        await inter.response.send_message(self.babel(inter, 'privatemessageonly'), **kwargs)
        return
      if isinstance(error, (commands.BotMissingPermissions, commands.MissingPermissions)):
        permlist = self.bot.babel.string_list(inter, [f'`{p}`' for p in error.missing_permissions])
        me = isinstance(error, commands.BotMissingPermissions)
        await inter.response.send_message(self.babel(inter, 'missingperms', me=me, perms=permlist), **kwargs)
        return
      if isinstance(error, commands.CommandInvokeError):
        if isinstance(error.original, self.bot.auth.AuthError):
          await inter.response.send_message(str(error.original), **kwargs)
          return
        await inter.response.send_message(self.babel(inter, 'commanderror', error=str(error.original)), **kwargs)
        raise error.original
      elif isinstance(error, (commands.CheckFailure, commands.CheckAnyFailure)):
        print("Unhandled error;", error)
        return
    except disnake.InteractionTimedOut:
      print(
        "Unable to handle error in command",
        inter.application_command.name,
        "because the interaction timed out."
      )
      print(error)


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Error(bot))
