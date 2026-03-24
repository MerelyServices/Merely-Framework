"""
  EventMsg - Automated messages triggered by events
  Generalized version of welcome and farewell
  Dependancies: Auth
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, Union, TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

from main import MerelyCog

if TYPE_CHECKING:
  from main import MerelyBot

getdatecomponent = [
  {
    'label': "Edit date",
    'custom_id': 'edit_date',
    'style': discord.ButtonStyle.secondary,
    'emoji': discord.PartialEmoji(name='📅')
  }
]


class Event():
  """
    The conditions of an event which the bot should watch for

    Event parameter cheat sheet;
    member
      mention
      name
    guild
      name
    role
      name
    channel
      name
      mention
    emoji
      name
    ban
      reason
    date
      date
      week
      month
      quarter
      year
      shortyear
    xp
      level
  """
  def __init__(
    self,
    name:str,
    usage:str,
    variables:tuple[str, ...],
    components:Optional[list[dict[str, discord.ui.Item]]] = None
  ) -> None:
    self.name = name
    self.example = usage
    self.variables = variables
    self.components = components # Additional custom components for this event

  def __str__(self) -> str:
    return self.name

  def __hash__(self) -> int:
    return hash(self.name)


@enum.unique
class Events(enum.Enum):
  # Built-in discord events, most require members scope
  WELCOME = Event(
    'on_member_join',
    "{member.mention} has joined {guild.name}!",
    ('member.mention', 'member.name', 'guild.name')
  ),
  FAREWELL = Event(
    'on_member_leave',
    "@{member.name} has left {guild.name}.",
    ('member.name', 'guild.name')
  ),
  ROLE_GAIN = Event(
    'on_member_update role add',
    "{member.mention} has been given the role {role.name}!",
    ('member.mention', 'member.name', 'role.name')
  ),
  ROLE_LOSE = Event(
    'on_member_update role remove',
    "{member.mention} has lost the role {role.name}!",
    ('member.mention', 'member.name', 'role.name')
  ),
  MESSAGE = Event(
    'on_message',
    "@{member.name} just posted in {channel.mention}",
    ('member.name', 'channel.mention')
  ), # Requires message content scope
  NEW_EMOJI = Event(
    'on_guild_emojis_update',
    "A new emoji has just been added; {emoji} - use it with :{emoji.name}:!",
    ('emoji', 'emoji.name')
  ),
  BAN = Event(
    'on_member_ban',
    "@{user.name} has been banned! Reason: {ban.reason}.",
    ('user.name', 'ban.reason')
  ),
  UNBAN = Event(
    'on_member_unban',
    "@{user.name}'s ban has been lifted!",
    ('user.name',)
  ),
  # Time system
  DAILY = Event(
    'on_day',
    "Daily post - {date.date}",
    ('date.date',),
    getdatecomponent
  ),
  WEEKLY = Event(
    'on_week',
    "Weekly post - {date.week}",
    ('date.date', 'date.week'),
    getdatecomponent
  ),
  MONTHLY = Event(
    'on_month',
    "Monthly post - {date.month}",
    ('date.date', 'date.month'),
    getdatecomponent
  ),
  QUARTERLY = Event(
    'on_quarter',
    "Quarterly post - Q{date.quarter}{date.shortyear}",
    ('date.date', 'date.quarter', 'date.year', 'date.shortyear'),
    getdatecomponent
  ),
  YEARLY = Event(
    'on_year',
    "Yearly post - {date.year}",
    ('date.date', 'date.year', 'date.shortyear'),
    getdatecomponent
  ),
  # XP system, does nothing unless XP module is enabled
  XP_UP = Event(
    'on_xp_up',
    "{member.mention} has gained XP; level {xp.level}, {xp} XP.",
    ('member.mention', 'member.name', 'xp.level', 'xp')
  ),
  LEVEL_UP = Event(
    'on_level_up',
    "{member.mention} is now level {xp.level}!",
    ('member.mention', 'member.name', 'xp.level', 'xp')
  )


class Action(enum.Enum):
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


class EventMsg(MerelyCog):
  """ Setup custom messages to send on an event """
  SCOPE = 'eventmsg'

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)

  def pop_msg_var(self, event:Event, message:str, **kwargs) -> str:
    """ Goes through allowed variables for this event and fills the string """
    newmessage = message
    for evar in event.variables:
      currentval: Optional[Union[
        discord.Member,discord.User,discord.Guild,discord.Role,discord.Emoji,Date
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

  @commands.Cog.listener("on_member_join")
  async def on_welcome(self, member:discord.Member):
    """welcome service, shows a custom welcome message to new users"""
    if f"{member.guild.id}_welcome" in self.config:
      data = self.config[f"{member.guild.id}_welcome"].split(', ')
      channel = member.guild.get_channel(int(data[0]))
      assert isinstance(channel, discord.abc.Messageable)
      await channel.send(
        ', '.join(data[1:]).format(member.mention, member.guild.name)
      )

  @commands.Cog.listener("on_raw_member_remove")
  async def on_farewell(self, payload:discord.RawMemberRemoveEvent):
    """farewell service, shows a custom farewell message whenever someone leaves"""
    if f"{payload.guild_id}_farewell" in self.config:
      data = self.config[f"{payload.guild_id}_farewell"].split(', ')
      guild = self.bot.get_guild(payload.guild_id)
      if guild is not None:
        channel = guild.get_channel(int(data[0]))
        assert isinstance(channel, discord.abc.Messageable)
        await channel.send(', '.join(data[1:]).format(f"{payload.user.name}", guild.name))

  class EventMessageEditor(discord.ui.Modal):
    """ Modal simply provides a text box to change the event message """
    def __init__(self, eventview:"EventMsg.EventEditView"):
      """ Create modal with the current message content """
      super().__init__(
        title="Edit event message",
        custom_id=f'{eventview.eid}_editor'
      )

      self.messageInput = discord.ui.TextInput(
        label="Message",
        custom_id='message',
        placeholder=eventview.message,
        default=eventview.message,
        style=discord.TextStyle.paragraph,
        min_length=1
      )
      self.add_item(self.messageInput)

      self.eventview = eventview

    async def on_submit(self, inter:discord.Interaction, /):
      """ Handle the new message content """
      self.eventview.message = self.messageInput.value
      await self.eventview.update(inter)

  class EventEditView(discord.ui.View):
    """ Controls and state for an EventMessage """
    def __init__(
      self,
      parent:"EventMsg",
      inter:discord.Interaction,
      event:Event,
      action:Action,
      message:str,
      xp:int,
      channel:discord.TextChannel,
      usage:str
    ):
      """ Create all buttons """
      super().__init__(timeout=60)

      self.parent = parent
      self.inter = inter
      self.event = event
      self.action = action
      self.channel = channel
      self.message = message
      self.xp = xp
      self.usage = usage
      self.eid = f"{channel.guild.id}_{channel.id}_{event.name}_{action.name}"

      # Build view
      match action:
        case Action.SEND_MESSAGE | Action.EDIT_MESSAGE:
          self.add_item(parent.bot.utilities.CallbackButton(
            callback=self.edit_click,
            label="Edit",
            style=discord.ButtonStyle.secondary,
            custom_id=f'{self.eid}_edit',
            emoji='✏️'
          ))
          if event.components:
            for comp in event.components:
              self.add_item(parent.bot.utilities.CallbackButton(
                callback=self.custom_click,
                **comp
              ))
        case Action.GRANT_XP:
          self.add_item(parent.bot.utilities.CallbackSelect(
            callback=self.custom_click,
            custom_id=f"{self.eid}_xpmult",
            placeholder="XP Points",
            options=range(1,25)
          ))
          if event.name == 'on_message':
            self.add_item(parent.bot.utilities.CallbackSelect(
              callback=self.custom_click,
              custom_id=f"{self.eid}_xpmode",
              placeholder="Mode",
              options={'Number (simple mode)': 0, 'Message length': 1}
            ))
        case _:
          raise AssertionError("An event was specified which was not handled in /eventmessage")

      self.submit_btn = parent.bot.utilities.CallbackButton(
        callback=self.submit_click,
        label="Submit",
        custom_id=f"{self.eid}_submit",
        style=discord.ButtonStyle.primary,
        emoji='✅',
        disabled=True
      )
      self.add_item(self.submit_btn)

    async def update(self, inter:discord.Interaction):
      """ Refresh the view, reflecting any changes made to variables """
      state = self.parent.babel(inter, 'event_controlpanel',
                                message=self.message,
                                channel=self.channel.mention,
                                xp=str(self.xp),
                                usage=self.usage)

      if self.message:
        self.submit_btn.disabled = False
      else:
        self.submit_btn.disabled = True

      await inter.response.edit_message(content=state, view=self)

    async def edit_click(self, inter:discord.Interaction):
      """ Opens the event message editor """
      await inter.response.send_modal(EventMsg.EventMessageEditor(self))

    async def submit_click(self, inter:discord.Interaction):
      """ Saves event to storage and finishes the interaction """
      pass

    async def custom_click(self, inter:discord.Interaction):
      """ Code to handle any other user input (Button or Select) """
      assert inter.custom_id is not None
      if inter.custom_id == 'edit_date':
        pass
      elif inter.custom_id.endswith('_xpmult'):
        pass
      elif inter.custom_id.endswith('_xpmode'):
        pass
      else:
        raise Exception(f"Unhandled click event '{inter.custom_id}'")

    async def on_timeout(self):
      for item in self.children:
        if isinstance(item, (discord.ui.Button, discord.ui.Select)):
          item.disabled = True
      await self.inter.response.edit_message(
        content=self.parent.bot.babel(self.inter, 'error', 'timeoutview'),
        view=self
      )

  @app_commands.command()
  @app_commands.describe(
    channel="The target channel where the event message will be sent",
    event="The event for the bot to watch for",
    action="The action the bot will take in response"
  )
  @app_commands.default_permissions(moderate_members=True)
  @commands.bot_has_permissions(read_messages=True, manage_messages=True)
  async def eventmessage(
    self,
    inter:discord.Interaction,
    channel:discord.TextChannel,
    event:Event,
    action:Action
  ):
    """
    Set up a message/action to take whenever something happens on the server.
    """
    # Default state
    usage = ''
    message = ''
    xp = 0
    if action in (Action.SEND_MESSAGE, Action.EDIT_MESSAGE):
      message = event.example
      usage = self.pop_msg_var(
        event=event,
        message='\n'.join(["`[["+evar+"]]` = {"+evar+"}" for evar in event.variables]),
        guild=channel.guild,
        member=inter.user,
        channel=channel,
        emoji=channel.guild.emojis[-1],
        role=channel.guild.roles[-1],
        date=Date(2023, 10, 28) # example date shows month and day numbers clearly
      ).replace('[[', '{').replace(']]', '}')
    elif action is Action.GRANT_XP:
      xp = 0
    elif action is Action.NOTHING:
      #TODO: remove saved eventmessage
      pass
    else:
      raise AssertionError(f"Unhandled action '{action.name}'!")

    state = self.babel(inter, 'event_controlpanel',
                       message=message,
                       channel=channel.mention,
                       xp=str(xp),
                       usage=usage)
    await inter.response.send_message(
      state,
      view=self.EventEditView(self, inter, event, action, message, xp, channel, usage),
      ephemeral=True,
      allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False)
    )

  welcome = app_commands.Group(
    name='welcome',
    description="An automation that posts a message whenever a user joins",
    guild_only=True,
    default_permissions=discord.Permissions(administrator=True)
  )

  @welcome.command(name='get')
  async def welcome_get(self, inter:discord.Interaction):
    """ Gets the current welcome message. Otherwise, gives instructions on how to set one """
    assert inter.guild is not None
    if f'{inter.guild.id}_welcome' in self.config:
      data = self.config[f"{inter.guild.id}_welcome"].split(', ')
      await inter.response.send_message(
          self.bot.babel(inter, 'greeter', 'greeting_preview',
                         channel=self.bot.get_partial_messageable(int(data[0])).mention,
                         message=', '.join(data[1:]).format('@USER', inter.guild.name)),
          ephemeral=True
        )
    else:
      await inter.response.send_message(
        self.bot.babel(inter, 'greeter', 'welcome_set_instructions'),
        ephemeral=True
      )

  @welcome.command(name='set')
  @app_commands.describe(message="The message that will be sent when a member joins.")
  async def welcome_set(self, inter:discord.Interaction, message:str):
    """
      Sets the welcome message based on your input.
    """
    assert inter.channel is not None and inter.guild is not None
    self.config[f'{inter.guild.id}_welcome'] = f"{inter.channel.id}, {message}"
    self.bot.config.save()
    await inter.response.send_message(
      self.bot.babel(inter, 'greeter', 'welcome_set_success')
    )

  @welcome.command(name='clear')
  async def welcome_clear(self, inter:discord.Interaction):
    """ Clears the welcome message """
    assert inter.guild is not None
    if f'{inter.guild.id}_welcome' in self.config:
      self.config.pop(f'{inter.guild.id}_welcome')
      self.bot.config.save()
      await inter.response.send_message(
        self.bot.babel(inter, 'greeter', 'welcome_clear_success')
      )
    else:
      await inter.response.send_message(
        self.bot.babel(inter, 'greeter', 'welcome_clear_failed')
      )

  farewell = app_commands.Group(
    name='farewell',
    description="An automation that posts a message whenever a user leaves",
    guild_only=True,
    default_permissions=discord.Permissions(administrator=True)
  )

  @farewell.command(name='get')
  async def farewell_get(self, inter:discord.Interaction):
    """ Gets the current farewell message. Otherwise, gives instructions on how to set one """
    assert inter.guild is not None
    if f'{inter.guild.id}_farewell' in self.config:
      data = self.config[f"{inter.guild.id}_farewell"].split(', ')
      await inter.response.send_message(
        self.bot.babel(inter, 'greeter', 'greeting_preview',
                       channel=self.bot.get_partial_messageable(int(data[0])).mention,
                       message=', '.join(data[1:]).format('USER#1234', inter.guild.name)),
        ephemeral=True
      )
    else:
      await inter.response.send_message(
        self.bot.babel(inter, 'greeter', 'farewell_set_instructions'),
        ephemeral=True
      )

  @farewell.command(name='set')
  @app_commands.describe(message="The message that will be sent when a member joins.")
  async def farewell_set(self, inter:discord.Interaction, message:str):
    """ Sets the welcome message based on your input. """
    assert inter.channel is not None and inter.guild is not None
    self.config[f'{inter.guild.id}_farewell'] = f"{inter.channel.id}, {message}"
    self.bot.config.save()
    await inter.response.send_message(self.bot.babel(inter, 'greeter', 'farewell_set_success'))

  @farewell.command(name='clear')
  async def farewell_clear(self, inter:discord.Interaction):
    """ Clears the farewell message """
    assert inter.guild is not None
    if f'{inter.guild.id}_farewell' in self.config:
      self.config.pop(f'{inter.guild.id}_farewell')
      self.bot.config.save()
      await inter.response.send_message(self.bot.babel(inter, 'greeter', 'farewell_clear_success'))
    else:
      await inter.response.send_message(self.bot.babel(inter, 'greeter', 'farewell_clear_failure'))


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(EventMsg(bot))
