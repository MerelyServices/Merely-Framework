"""
  EventMsg - Automated messages triggered by events
  Generalized version of welcome and farewell
  Dependancies: Auth
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Union
import disnake
from disnake.ext import commands

getdatecomponent = [
  disnake.ui.Button(
    label="Edit date",
    custom_id='edit_date',
    style=disnake.ButtonStyle.secondary,
    emoji=disnake.PartialEmoji(name='📅')
  )
]

class Event():
  """ The conditions of an event which the bot should watch for """
  def __init__(
    self,
    name:str,
    usage:str,
    variables:tuple[str],
    components:Optional[list[disnake.Component]]=[]
  ) -> None:
    self.name = name
    self.example = usage
    self.variables = variables
    self.components = components # Additional custom components for this event

Events = {
  # Built-in disnake events, most require members scope
  'WELCOME': Event(
    'on_member_join',
    "{member.mention} has joined {guild.name}!",
    ('member.mention', 'member.name', 'guild.name')
  ),
  'FAREWELL': Event(
    'on_member_leave',
    "{member.name}#{member.discriminator} has left {guild.name}.",
    ('member.name', 'member.discriminator', 'guild.name')
  ),
  'ROLE_GAIN': Event(
    'on_member_update role add',
    "{member.mention} has been given the role {role.name}!",
    ('member.mention', 'member.name', 'role.name')
  ),
  'ROLE_LOSE': Event(
    'on_member_update role remove',
    "{member.mention} has lost the role {role.name}!",
    ('member.mention', 'member.name', 'role.name')
  ),
  'MESSAGE': Event(
    'on_message',
    "{member.name} just posted in {channel.mention}",
    ('member.name', 'channel.mention')
  ), # Requires message content scope
  'NEW_EMOJI': Event(
    'on_guild_emojis_update',
    "A new emoji has just been added; {emoji} - use it with :{emoji.name}:!",
    ('emoji', 'emoji.name')
  ),
  'BAN': Event(
    'on_member_ban',
    "{user.name}#{user.discriminator} has been banned! Reason: {ban.reason}.",
    ('user.name', 'user.discriminator', 'ban.reason')
  ),
  'UNBAN': Event(
    'on_member_unban',
    "{user.name}#{user.disciminator}'s ban has been lifted!",
    ('user.name', 'user.discriminator')
  ),
  # Time system
  'DAILY': Event(
    'on_day',
    "Daily post - {date.date}",
    ('date.date',),
    getdatecomponent
  ),
  'WEEKLY': Event(
    'on_week',
    "Weekly post - {date.week}",
    ('date.date', 'date.week'),
    getdatecomponent
  ),
  'MONTHLY': Event(
    'on_month',
    "Monthly post - {date.month}",
    ('date.date', 'date.month'),
    getdatecomponent
  ),
  'QUARTERLY': Event(
    'on_quarter',
    "Quarterly post - Q{date.quarter}{date.shortyear}",
    ('date.date', 'date.quarter', 'date.year', 'date.shortyear'),
    getdatecomponent
  ),
  'YEARLY': Event(
    'on_year',
    "Yearly post - {date.year}",
    ('date.date', 'date.year', 'date.shortyear'),
    getdatecomponent
  ),
  # XP system, does nothing unless XP module is enabled
  'XP_UP': Event(
    'on_xp_up',
    "{member.mention} has gained XP; level {xp.level}, {xp} XP.",
    ('member.mention', 'member.name', 'xp.level', 'xp')
  ),
  'LEVEL_UP': Event(
    'on_level_up',
    "{member.mention} is now level {xp.level}!",
    ('member.mention', 'member.name', 'xp.level', 'xp')
  )
}

class Action(Enum):
  """ Actions that can be performed on an event """
  NOTHING = 0
  SEND_MESSAGE = 1
  EDIT_MESSAGE = 2
  GRANT_XP = 3

class Date(datetime):
  """
  This is a modified datetime class which adds some easy formatting properties for strings
  """
  @property
  def date(self) -> str:
    """ Override for date, returns D/MM/YYYY """
    return f"<t:{round(self.timestamp())}:d>"
  @property
  def week(self) -> int:
    """ Week number (0-52) """
    return int(self.strftime('%W'))
  @property
  def quarter(self) -> int:
    """ Quarter number (1-4) as in Q422 """
    return {1:1, 2:1, 3:1, 4:2, 5:2, 6:2, 7:3, 8:3, 9:3, 10:4, 11:4, 12:4}[self.month]
  @property
  def shortyear(self) -> int:
    """ 2 digit representaion of the current year (0-99) """
    return self.year % 100

class EventMsg(commands.Cog):
  """ Setup custom messages to send on an event """
  def __init__(self, bot:commands.Bot):
    self.bot = bot
    if not bot.config.getboolean('extensions', 'auth', fallback=False):
      raise AssertionError("'auth' must be enabled to use 'eventmsg'")
    if not bot.config.getboolean('extensions', 'help', fallback=False):
      print(Warning("'help' is a recommended extension for 'eventmsg'"))
    # ensure config file has required data
    if not bot.config.has_section('eventmsg'):
      bot.config.add_section('eventmsg')

  def pop_msg_var(self, event:Event, message:str, **kwargs) -> str:
    """ Goes through allowed variables for this event and fills the string """
    newmessage = message
    for evar in event.variables:
      currentval: Optional[Union[
        disnake.Member,disnake.User,disnake.Guild,disnake.Role,disnake.Emoji,Date
      ]] = None
      evarparts = evar.split('.')
      if evarparts[0] in kwargs and kwargs[evarparts[0]] is not None:
        currentvar = kwargs[evarparts[0]]
        if len(evarparts) > 1:
          if evarparts[1] in dir(currentvar):
            currentval = getattr(currentvar, evarparts[1])
          else:
            raise AssertionError(f".{evarparts[1]} was not found in {evarparts[0]}!")
        else:
          currentval = currentvar
        if currentval is not None:
          newmessage = newmessage.replace("{"+evar+"}", str(currentval))
        else:
          print(f"WARN: Missing variable {evar} for event (value is None)")
      else:
        print(f"WARN: Missing variable {evar} for event (was not in kwargs)")
    return newmessage

  @commands.Cog.listener("on_raw_member_join")
  async def on_welcome(self, member:disnake.Member):
    """welcome service, shows a custom welcome message to new users"""
    if f"{member.guild.id}_welcome" in self.bot.config['eventmsg']:
      data = self.bot.config['eventmsg'][f"{member.guild.id}_welcome"].split(', ')
      channel = member.guild.get_channel(int(data[0]))
      await channel.send(', '.join(data[1:]).format(member.mention, member.guild.name))

  @commands.Cog.listener("on_raw_member_leave")
  async def on_farewell(self, payload:disnake.RawGuildMemberRemoveEvent):
    """farewell service, shows a custom farewell message whenever someone leaves"""
    if f"{payload.guild_id}_farewell" in self.bot.config['eventmsg']:
      data = self.bot.config['eventmsg'][f"{payload.guild_id}_farewell"].split(', ')
      guild = self.bot.get_guild(payload.guild_id)
      channel = guild.get_channel(int(data[0]))
      await channel.send(', '.join(data[1:])
                         .format(f"{payload.user.name}#{payload.user.discriminator}", guild.name))

  @commands.slash_command()
  async def eventmessage(
    self,
    inter:disnake.GuildCommandInteraction,
    channel:disnake.TextChannel,
    raw_event:str = commands.Param(name='event', choices=list(Events)),
    raw_action:Action = commands.Param(name='action')
  ):
    """
    Set up a message/action to take whenever something happens on the server.

    Parameters
    ----------
    channel: The target channel where the event message will be sent
    event: The event for the bot to watch for
    action: The action the bot will take in response
    """
    event = Events[raw_event]
    action = Action(raw_action)

    components = [disnake.ui.ActionRow()]
    mainrow = 0
    match action:
      case Action.SEND_MESSAGE | Action.EDIT_MESSAGE:
        components[0].add_button(
          label="Edit message",
          custom_id=f"action_{raw_action}_edit",
          style=disnake.ButtonStyle.secondary,
          emoji='📝'
        )
        for comp in event.components:
          if comp is disnake.ui.Button:
            components[mainrow].append_item(comp)
          else:
            components.insert(0, disnake.ui.ActionRow(*(comp,)))
            mainrow += 1
      case Action.GRANT_XP:
        components.insert(0, disnake.ui.ActionRow())
        mainrow += 1
        components[0].add_select(
          custom_id=f"action_{raw_action}_value",
          placeholder="XP Points",
          options=range(1,25)
        )
        if raw_event == 'MESSAGE':
          components.insert(1, disnake.ui.ActionRow())
          mainrow += 1
          components[1].add_select(
            custom_id=f"action_{raw_action}_mode",
            placeholder="Mode",
            options={'Number (simple mode)': 0, 'Message length': 1}
          )
      case _:
        raise AssertionError("An event was specified which was not handled in /eventmessage")
    components[mainrow].add_button(
      label="Submit",
      custom_id=f"{inter.guild_id}_{channel.id}_{raw_event}",
      style=disnake.ButtonStyle.primary,
      emoji='✅',
      disabled=True
    )

    usage = ''
    message = ''
    xp=0
    if action in (Action.SEND_MESSAGE, Action.EDIT_MESSAGE):
      usage = self.pop_msg_var(
        event=event,
        message='\n'.join(["`[["+evar+"]]` = {"+evar+"}" for evar in event.variables]),
        guild=inter.guild,
        member=inter.user,
        channel=channel,
        emoji=inter.guild.emojis[-1],
        role=inter.guild.roles[-1],
        date=Date(2023, 10, 28) # example date shows month and day numbers clearly
      ).replace('[[', '{').replace(']]', '}')
      
      message = event.example

    await inter.response.send_message(self.bot.babel(
      inter,
      'eventmsg',
      'event_controlpanel',
      message=message,
      channel=channel.mention,
      xp=xp,
      usage=usage
    ), components=components, ephemeral=True, allowed_mentions=[])

  @commands.group()
  @commands.guild_only()
  async def welcome(self, ctx:commands.Context):
    """welcome setter / getter"""
    if ctx.invoked_subcommand is None:
      raise commands.BadArgument
  @welcome.command(name='get')
  async def welcome_get(self, ctx:commands.Context):
    if f'{ctx.guild.id}_welcome' in self.bot.config['eventmsg']:
      data = self.bot.config['eventmsg'][f"{ctx.guild.id}_welcome"].split(', ')
      await ctx.reply(self.bot.babel(ctx, 'eventmsg', 'greeting_preview', channel=ctx.guild.get_channel(int(data[0])).mention, message=', '.join(data[1:]).format('@USER', ctx.guild.name)))
    else:
      await self.welcome_set(ctx)
  @welcome.command(name='set')
  async def welcome_set(self, ctx:commands.Context, *, message:str=''):
    self.bot.cogs['Auth'].admins(ctx.message)
    if not message:
      await ctx.reply(self.bot.babel(ctx, 'eventmsg', 'welcome_set_instructions'))
    else:
      self.bot.config['eventmsg'][f'{ctx.guild.id}_welcome'] = f"{ctx.channel.id}, {message}"
      self.bot.config.save()
      await ctx.reply(self.bot.babel(ctx, 'eventmsg', 'welcome_set_success'))
  @welcome.command(name='clear')
  async def welcome_clear(self, ctx:commands.Context):
    self.bot.cogs['Auth'].admins(ctx.message)
    if f'{ctx.guild.id}_welcome' in self.bot.config['eventmsg']:
      self.bot.config.remove_option('eventmsg', f'{ctx.guild.id}_welcome')
      self.bot.config.save()
      await ctx.reply(self.bot.babel(ctx, 'eventmsg', 'welcome_clear_success'))
    else:
      await ctx.reply(self.bot.babel(ctx, 'eventmsg', 'welcome_clear_failed'))

  @commands.group()
  @commands.guild_only()
  async def farewell(self, ctx:commands.Context):
    """getter / setter for farewell"""
    if ctx.invoked_subcommand is None:
      raise commands.BadArgument
  @farewell.command(name='get')
  async def farewell_get(self, ctx:commands.Context):
    if f'{ctx.guild.id}_farewell' in self.bot.config['eventmsg']:
      data = self.bot.config['eventmsg'][f"{ctx.guild.id}_farewell"].split(', ')
      await ctx.reply(self.bot.babel(ctx, 'eventmsg', 'greeting_preview', channel=ctx.guild.get_channel(int(data[0])).mention, message=', '.join(data[1:]).format('USER#1234', ctx.guild.name)))
    else:
      await self.farewell_set(ctx)
  @farewell.command(name='set')
  async def farewell_set(self, ctx:commands.Context, *, message:str=''):
    self.bot.cogs['Auth'].admins(ctx.message)
    if not message:
      await ctx.reply(self.bot.babel(ctx, 'eventmsg', 'farewell_set_instructions'))
    else:
      self.bot.config['eventmsg'][f'{ctx.guild.id}_farewell'] = f"{ctx.channel.id}, {message}"
      self.bot.config.save()
      await ctx.reply(self.bot.babel(ctx, 'eventmsg', 'farewell_set_success'))
  @farewell.command(name='clear')
  async def farewell_clear(self, ctx:commands.Context):
    self.bot.cogs['Auth'].admins(ctx.message)
    if f'{ctx.guild.id}_farewell' in self.bot.config['eventmsg']:
      self.bot.config.remove_option('eventmsg', f'{ctx.guild.id}_farewell')
      self.bot.config.save()
      await ctx.reply(self.bot.babel(ctx, 'eventmsg', 'farewell_clear_success'))
    else:
      await ctx.reply(self.bot.babel(ctx, 'eventmsg', 'farewell_clear_failure'))


def setup(bot:commands.Bot):
  bot.add_cog(EventMsg(bot))