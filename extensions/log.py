"""
  Log - User activity recording and error tracing
  Features: to file, to channel, command, responses to a command, errors, misc
  Recommended cogs: Error
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
import disnake
from disnake.ext import commands

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

  def wrap(self, content:str, author:disnake.User, channel:disnake.abc.Messageable, maxlen:int = 80):
    """ Format log data consistently """
    # Shorthand for truncate because it's used so many times
    truncate = self.bot.utilities.truncate
    if isinstance(channel, disnake.TextChannel):
      return ' '.join((
        f"[{truncate(channel.guild.name, 10)}#{truncate(channel.name, 20)}]",
        f"{truncate(author.name, 10)}#{author.discriminator}: {truncate(content, maxlen)}"
      ))
    if isinstance(channel, disnake.DMChannel):
      if channel.recipient:
        return ' '.join((
          f"[DM({truncate(channel.recipient.name, 10)}#{channel.recipient.discriminator})]",
          f"{author.name}#{author.discriminator}: {truncate(content, maxlen)}"
        ))
      return (
        f"[DM] {truncate(author.name, 10)}#{author.discriminator}: {truncate(content, maxlen)}"
      )
    if isinstance(channel, disnake.Thread):
      channelname = f"{truncate(channel.guild.name, 10)}#{truncate(channel.parent.name, 20)}"
      return ' '.join((
        f"[{channelname}/{truncate(channel.name, 20)}]",
        f"{truncate(author.name, 10)}#{author.discriminator}:",
        f"{truncate(content, maxlen)}"
      ))
    return (
      f"[Unknown] {truncate(author.name, 10)}#{author.discriminator}: {truncate(content, maxlen)}"
    )

  @commands.Cog.listener('on_application_command')
  async def log_slash_command(self, inter:disnake.CommandInteraction):
    """ Record slash command calls """
    truncate = self.bot.utilities.truncate
    options = [f"{opt.name}:{truncate(str(opt.value), 30)}" for opt in inter.data.options]
    logentry = self.wrap(
      f"/{inter.data.name} {' '.join(options)}",
      inter.author,
      inter.channel
    )
    print(logentry)
    if self.logchannel:
      await self.logchannel.send(logentry)

  @commands.Cog.listener('on__slash_command_completion')
  async def log_slash_response(self, inter:disnake.CommandInteraction):
    """ Record any replies to a command """
    if not inter.response.is_done():
      return
    responses:list[disnake.Message] = []
    originalmsg = await inter.original_message()
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

  async def log_misc_message(self, msg:disnake.Message):
    """ Record a message that is in some way related to a command """
    logentry = self.wrap(msg.content, msg.author, msg.channel)
    print(logentry)
    if self.logchannel:
      await self.logchannel.send(logentry, embed=msg.embeds[0] if msg.embeds else None)

  async def log_misc_str(self, inter:disnake.Interaction, content:str):
    """ Record a string and interaction separately """
    logentry = self.wrap(content, inter.author, inter.channel)
    print(logentry)
    if self.logchannel:
      await self.logchannel.send(logentry)


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(Log(bot))
