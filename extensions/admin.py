"""
  Admin - Powerful commands for administrators
  Features: clean, purge, and autodelete
  Dependancies: Auth
"""

from __future__ import annotations

import asyncio
from enum import Enum
from typing import Optional, TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


class JanitorMode(int, Enum):
  """ Actions users can take to configure the janitor """
  DELETE_BOT = 0
  DELETE_ALL = 1
  DISABLED = -1


class Admin(commands.Cog):
  """ Admin tools """
  SCOPE = 'admin'

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)

  def check_delete(self, message:discord.Message, strict:bool = False):
    """ Criteria for message deletion """
    return (
      not message.flags.ephemeral and
      (
        strict or
        (
          message.author == self.bot.user or
          message.author.bot or
          message.content.startswith('<@'+str(self.bot.user.id)+'>') or
          message.type == discord.MessageType.pins_add
        )
      )
    )

  @commands.Cog.listener("on_message")
  async def janitor_autodelete(self, message:discord.Message):
    """janitor service, deletes messages after 30 seconds"""
    if f"{message.channel.id}_janitor" in self.config:
      strict = int(self.config.get(f"{message.channel.id}_janitor"))
      if self.check_delete(message, strict):
        await asyncio.sleep(30)
        await message.delete()

  @app_commands.command()
  @app_commands.describe(mode="Choose whether to have janitor enabled or disabled in this channel")
  @app_commands.default_permissions(administrator=True)
  @commands.bot_has_permissions(read_messages=True, manage_messages=True)
  async def janitor(
    self, inter:discord.Interaction, mode:JanitorMode
  ):
    """
      Add or remove janitor from this channel. Janitor deletes messages after 30 seconds
    """
    if mode != JanitorMode.DISABLED:
      self.config[f'{inter.channel.id}_janitor'] = str(int(mode))
      self.bot.config.save()
      await inter.response.send_message(self.babel(inter, 'janitor_set_success'))
    else:
      self.config.pop(f'{inter.channel.id}_janitor')
      self.bot.config.save()
      await inter.response.send_message(self.babel(inter, 'janitor_unset_success'))

  @app_commands.command()
  @app_commands.describe(
    number="The number of messages to search through, defaults to 50",
    clean_to="Searches through message history until this message is reached",
    strict="A strict clean, when enabled, deletes all messages by all users"
  )
  @app_commands.default_permissions(moderate_members=True)
  @commands.bot_has_permissions(read_messages=True, manage_messages=True)
  async def clean(
    self,
    inter:discord.Interaction,
    number:Optional[app_commands.Range[int, 1, 10000]],
    clean_to:Optional[app_commands.Range[str, 10, 32]] = None,
    strict:bool = False
  ):
    """
      Clean messages from this channel. By default, this only deletes messages to and from this bot.
    """
    try:
      await inter.response.defer(thinking=True)
      if clean_to:
        deleted = await inter.channel.purge(
          limit=number if number else 1000,
          check=lambda m: self.check_delete(m, strict),
          after=discord.Object(int(clean_to) - 1)
        )
      else:
        deleted = await inter.channel.purge(
          limit=number if number else 50,
          check=lambda m: self.check_delete(m, strict),
          before=await inter.original_response()
        )
      await inter.followup.send(self.babel(inter, 'clean_success', n=len(deleted)))
    except discord.errors.Forbidden:
      await inter.followup.send(self.babel(inter, 'clean_failed'))


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Admin(bot))
