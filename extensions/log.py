"""
  Log - User activity recording and error tracing
  Features: to file, to channel, command, responses to a command, errors, misc
  Recommended cogs: Error
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


class Log(commands.Cog):
  """ Record messages, commands and errors to file or a discord channel """
  SCOPE = 'log'

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    self.logchannel = None
    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)
    if 'logchannel' not in bot.config[self.SCOPE]:
      bot.config[self.SCOPE]['logchannel'] = ''

  @commands.Cog.listener('on_ready')
  async def get_logchannel(self):
    """ Connect to the logging channel """
    if self.config['logchannel'].isdigit():
      await asyncio.sleep(10) # Wait to reduce flood of requests on ready
      self.logchannel = await self.bot.fetch_channel(int(self.config['logchannel']))

  def wrap(self, content:str, author:discord.User, channel:discord.abc.Messageable, maxlen:int = 80):
    """ Format log data consistently """
    # Shorthand for truncate because it's used so many times
    truncate = self.bot.utilities.truncate
    if isinstance(channel, discord.TextChannel):
      return ' '.join((
        f"[{truncate(channel.guild.name, 10)}#{truncate(channel.name, 20)}]",
        f"{truncate(author.name, 10)}#{author.discriminator}: {truncate(content, maxlen)}"
      ))
    if isinstance(channel, discord.DMChannel):
      if channel.recipient:
        return ' '.join((
          f"[DM({truncate(channel.recipient.name, 10)}#{channel.recipient.discriminator})]",
          f"{author.name}#{author.discriminator}: {truncate(content, maxlen)}"
        ))
      return (
        f"[DM] {truncate(author.name, 10)}#{author.discriminator}: {truncate(content, maxlen)}"
      )
    if isinstance(channel, discord.Thread):
      channelname = f"{truncate(channel.guild.name, 10)}#{truncate(channel.parent.name, 20)}"
      return ' '.join((
        f"[{channelname}/{truncate(channel.name, 20)}]",
        f"{truncate(author.name, 10)}#{author.discriminator}:",
        f"{truncate(content, maxlen)}"
      ))
    return (
      f"[Unknown] {truncate(author.name, 10)}#{author.discriminator}: {truncate(content, maxlen)}"
    )

  @commands.Cog.listener('on_interaction')
  async def log_slash_command(self, inter:discord.Interaction):
    """ Record slash command calls """
    #TODO: maybe log button presses too?
    if inter.type != discord.InteractionType.application_command:
      return
    if 'options' not in inter.data:
      return
    truncate = self.bot.utilities.truncate
    options = []
    for raw_option in inter.data.get('options', []):
      options.append(
        raw_option['name'] + (':'+truncate(raw_option['value'], 30) if 'value' in raw_option else '')
      )
    cmdname = inter.command.root_parent.name if inter.command.root_parent else inter.command.name
    logentry = self.wrap(
      f"/{cmdname} {' '.join(options)}",
      inter.user,
      inter.channel
    )
    print(logentry)
    if self.logchannel:
      await self.logchannel.send(logentry)

  @commands.Cog.listener('on_app_command_completion')
  async def log_slash_response(
    self, inter:discord.Interaction, _:app_commands.Command | app_commands.ContextMenu
  ):
    """ Record any replies to a command """
    if not inter.response.is_done():
      return
    responses:list[discord.Message] = []
    if not inter.is_expired():
      return # This interaction isn't complete yet
    originalmsg = await inter.original_response()
    # Prevent errors if message history won't be available
    if isinstance(inter.channel, discord.DMChannel):
      if self.bot.user not in inter.channel.recipients: # This is somebody else's DMs
        return
    elif inter.guild:
      member = inter.guild.get_member(self.bot.user.id)
      if member is None: # This is somebody else's server
        # Curiously, the API seems to create a fake member just so this state isn't reached
        return
      if not inter.channel.permissions_for(member).read_message_history:
        # Can't read message history here
        return
    async for msg in inter.channel.history(after=originalmsg):
      if msg.author == self.bot.user and\
        msg.reference and\
        msg.reference.message_id == originalmsg.id:
        responses.append(msg)
    for response in responses:
      logentry = self.wrap(response.content, response.author, response.channel)
      print(logentry)
      if self.logchannel:
        await self.logchannel.send(logentry, embed=response.embeds[0] if response.embeds else None)

  async def log_misc_message(self, msg:discord.Message):
    """ Record a message that is in some way related to a command """
    logentry = self.wrap(msg.content, msg.author, msg.channel)
    print(logentry)
    if self.logchannel:
      await self.logchannel.send(logentry, embed=msg.embeds[0] if msg.embeds else None)

  async def log_misc_str(self, inter:discord.Interaction, content:str):
    """ Record a string and interaction separately """
    logentry = self.wrap(content, inter.user, inter.channel)
    print(logentry)
    if self.logchannel:
      await self.logchannel.send(logentry)


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Log(bot))
