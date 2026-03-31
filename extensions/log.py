"""
  Log - User activity recording and error tracing
  Features: to file, to channel, command, responses to a command, errors, misc
  Recommended cogs: Error
"""

from __future__ import annotations

import asyncio, re
from typing import TYPE_CHECKING, cast
import discord
from discord import app_commands
from discord.ext import commands

from main import MerelyCog

if TYPE_CHECKING:
  from main import MerelyBot


class Log(MerelyCog):
  """ Record messages, commands and errors to file or a discord channel """
  SCOPE = 'log'

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    self.logchannel:discord.abc.Messageable | None = None
    self.discord_url_filter = re.compile(r'^https://[^/]*discord[^/]*(/.*)$')
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
      logchannel = await self.bot.fetch_channel(int(self.config['logchannel']))
      assert isinstance(logchannel, discord.abc.Messageable)
      self.logchannel = logchannel

  def wrap(
    self,
    content:str,
    author:discord.User | discord.Member,
    channel:discord.abc.Messageable,
    maxlen:int = 80
  ):
    """ Format log data consistently """
    # Shorthand for truncate because it's used so many times
    truncate = self.bot.utilities.truncate
    if isinstance(channel, discord.TextChannel):
      return ' '.join((
        f"[{truncate(channel.guild.name, 10)}#{truncate(channel.name, 20)}]",
        f"{truncate(author.name, 15)}: {truncate(content, maxlen)}"
      ))
    if isinstance(channel, discord.DMChannel):
      if channel.recipient:
        return ' '.join((
          f"[DM({truncate(channel.recipient.name, 15)})]",
          f"{author.name}: {truncate(content, maxlen)}"
        ))
      return (
        f"[DM] {truncate(author.name, 15)}: {truncate(content, maxlen)}"
      )
    if isinstance(channel, discord.Thread):
      channelname = (
        truncate(channel.guild.name, 10) + '#' +
        truncate(channel.parent.name if channel.parent else '', 20)
      )
      return ' '.join((
        f"[{channelname}/{truncate(channel.name, 20)}]",
        f"{truncate(author.name, 15)}:",
        f"{truncate(content, maxlen)}"
      ))
    return (
      f"[Unknown] {truncate(author.name, 15)}: {truncate(content, maxlen)}"
    )

  @commands.Cog.listener('on_interaction')
  async def log_slash_command(self, inter:discord.Interaction):
    """ Record slash commands, context menu commands, modal submissions, and button presses """
    if inter.type not in (
      discord.InteractionType.application_command, discord.InteractionType.modal_submit,
      discord.InteractionType.component
    ):
      return
    truncate = self.bot.utilities.truncate

    # Find command name, if any
    cmdname = ''
    options = []
    if isinstance(inter.command, app_commands.Command):
      cmdname = '/' + (
        inter.command.root_parent.name if inter.command.root_parent else inter.command.name
      )
    elif isinstance(inter.command, app_commands.ContextMenu):
      assert inter.data is not None and 'target_id' in inter.data
      cmdname = inter.command.name
      target = inter.data['target_id']
      assert target is not None
      if inter.data['type'] == 2:
        assert 'resolved' in inter.data
        resolved = inter.data['resolved']
        assert resolved is not None
        users = cast(dict[str, discord.User], resolved.get('users'))
        options.append('target:@' + users[str(target)].name)
      elif inter.data['type'] == 3:
        assert isinstance(inter.channel, discord.TextChannel)
        target_message = inter.channel.get_partial_message(int(target))
        options.append('target:'+target_message.jump_url[19:])
      else:
        options.append('target: unknown')
    elif inter.type == discord.InteractionType.modal_submit:
      cmdname = 'Modal submit'
    elif inter.type == discord.InteractionType.component:
      cmdname = 'Button click'
    else:
      cmdname = 'Unknown command'

    # Find parameters and values, if any
    if inter.data is None:
      return
    if 'options' in inter.data:
      for opt in inter.data['options']:
        value = ''
        if 'value' in opt:
          if matches := re.match(self.discord_url_filter, str(opt['value'])):
            value = ':' + matches.group(1)
          else:
            value = ':' + truncate(opt['value'], 30)
        options.append(opt['name'] + value)
    elif 'values' in inter.data:
      pre = ':'
      if inter.type == discord.InteractionType.component:
        cmdname = 'Selection'
        pre = inter.data['custom_id'] + ':'
      for value in inter.data['values']:
        if matches := re.match(self.discord_url_filter, str(value)):
          value = pre + matches.group(1)
        else:
          value = pre + truncate(value, 30)
        options.append(value)
    elif 'components' in inter.data:
      for row in inter.data['components']:
        if 'components' in row:
          subcomponents = row['components']
          for opt in subcomponents:
            options.append(
              opt['custom_id'] + (':' + truncate(opt['value'], 30) if 'value' in opt else '')
            )
          if 'value' in row:
            options.append(row['custom_id'] + (':' + truncate(row['value'],30)))
        else:
          continue
    elif 'custom_id' in inter.data:
      options.append(truncate(inter.data['custom_id'], 30))

    # Compile results together
    assert isinstance(inter.channel, discord.abc.Messageable)
    logentry = self.wrap(
      f"{cmdname} > {' '.join(options)}",
      inter.user,
      inter.channel,
      maxlen=250
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
    assert inter.channel is not None
    if isinstance(inter.channel, discord.DMChannel):
      if self.bot.user not in inter.channel.recipients: # This is somebody else's DMs
        return
    elif inter.guild and self.bot.user:
      member = inter.guild.get_member(self.bot.user.id)
      if member is None: # This is somebody else's server
        # Curiously, the API seems to create a fake member just so this state isn't reached
        return
      if not inter.channel.permissions_for(member).read_message_history:
        # Can't read message history here
        return
    if not isinstance(inter.channel, discord.abc.Messageable):
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
        kwargs: dict = {'embed': response.embeds[0]} if response.embeds else {}
        await self.logchannel.send(logentry, **kwargs)

  async def log_misc_message(self, msg:discord.Message):
    """ Record a message that is in some way related to a command """
    logentry = self.wrap(msg.content, msg.author, msg.channel)
    print(logentry)
    if self.logchannel:
      kwargs: dict = {'embed': msg.embeds[0]} if msg.embeds else {}
      await self.logchannel.send(logentry, **kwargs)

  async def log_misc_str(self, content:str = '', *, inter:discord.Interaction | None = None):
    """ Record a string and interaction separately """
    if inter:
      assert isinstance(inter.channel, discord.abc.Messageable)
      logentry = self.wrap(content, inter.user, inter.channel)
    else:
      logentry = content
    print(logentry)
    if self.logchannel:
      await self.logchannel.send(logentry)


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Log(bot))
