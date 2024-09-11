"""
  Announce - Direct messaging of important bot news to server owners and other subscribed users
"""

from __future__ import annotations

import base64, asyncio
from typing import TYPE_CHECKING
import disnake
from disnake.ext import commands

from extensions.controlpanel import Listable

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


# Stateless functions

def encode_uid(uid:int) -> str:
  """ Takes discord id and encodes it using ascii """
  return base64.b64encode(uid.to_bytes(8, 'big')).decode('ascii').replace('=','')


def decode_uid(uid:str) -> int | None:
  """ Takes encoded uid and returns id number """
  if len(uid) == 11:
    uid += '='
  try:
    return int.from_bytes(base64.b64decode(uid), 'big')
  except Exception:
    print(f"WARN: {uid} is not a valid encoded UID.")
    return None


def add_to_failed(failed:dict[str, list[str]], key:str, new:str):
  """ Adds to key or creates a new key for failed as needed """
  if key in failed:
    failed[key].append(new)
  else:
    failed[key] = [new]
  return failed


class Announce(commands.Cog):
  """ Handles DM announcements and ensures the process can resume after a crash or restart """
  SCOPE = 'announce'
  lock = False

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    #NOTE: This module should not be translated.
    self.bot = bot

    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)
    if 'in_progress' not in self.config:
      self.config['in_progress'] = ''
    if 'dm_subscription' not in self.config:
      self.config['dm_subscription'] = ''
    if 'subscription_history' not in self.config:
      self.config['subscription_history'] = ''

    # Restrict usage of these commands to specified guilds
    if bot.config['auth']['botadmin_guilds']:
      guilds = bot.config['auth']['botadmin_guilds']
      botadmin_guilds = [int(guild) for guild in guilds.split(' ')]
      for cmd in self.get_application_commands():
        cmd.guild_ids = botadmin_guilds
    elif not bot.quiet:
      print("  WARN: No botadmin_guilds defined, so all servers will be able to see system commands!")

  def controlpanel_settings(self, inter:disnake.Interaction):
    # ControlPanel integration
    return [Listable(self.SCOPE, 'dm_subscription', 'dm_subscription', encode_uid(inter.user.id))]

  def controlpanel_theme(self) -> tuple[str, disnake.ButtonStyle]:
    # Controlpanel custom theme for buttons
    return (self.SCOPE, disnake.ButtonStyle.red)

  # Events

  def subscribe(self, user_id:int) -> bool:
    # Subscribes users if they have never been subscribed before
    uid = encode_uid(user_id)
    if (
      uid+',' not in self.config['subscription_history']
      and uid+',' not in self.config['dm_subscription']
    ):
      self.config['dm_subscription'] += f'{uid},'
      self.config['subscription_history'] += f'{uid},'
      return True
    return False

  def unsubscribe(self, user_id:int) -> bool:
    # Unsubscribes a user if they are subscribed
    uid = encode_uid(user_id)
    if uid in self.config['dm_subscription']:
      self.config['dm_subscription'] = self.config['dm_subscription'].replace(uid+',', '')
    return False

  @commands.Cog.listener('on_ready')
  async def catchup(self):
    await asyncio.sleep(5) # Wait to reduce flood of commands on connect

    # Enable resume button if an announcement was in progress
    if self.config['in_progress']:
      raw_channel_id, raw_message_id = self.config['in_progress'].split('/')
      channel = self.bot.get_channel(int(raw_channel_id))
      try:
        msg = await channel.fetch_message(int(raw_message_id))
      except disnake.NotFound:
        self.config['in_progress'] = ''
        self.bot.config.save()
        print("Stopped tracking existing announcement because it was deleted")
      else:
        buttons:list[disnake.Button] = [self.SendButton(), self.ResumeButton()]
        buttons[0].disabled = True
        await msg.edit(components=buttons)

  @commands.Cog.listener('on_message_delete')
  async def on_cancel(self, msg:disnake.Message):
    if self.config['in_progress'] and f'{msg.channel.id}/{msg.id}' == self.config['in_progress']:
      self.config['in_progress'] = ''
      self.bot.config.save()
      print("Stopped tracking existing announcement because it was deleted")

  @commands.Cog.listener('on_guild_update')
  async def verify_owner(self, _:disnake.Guild, guild:disnake.Guild):
    # This indicates a guild owner might be active
    # Check they're subscribed, in case they weren't found earlier
    if guild.owner_id:
      if self.subscribe(guild.owner_id):
        self.bot.config.save()
    else:
      print("No owner found")

  @commands.Cog.listener('on_guild_join')
  async def autosubscribe(self, guild:disnake.Guild):
    if self.subscribe(guild.owner_id):
      self.bot.config.save()

  @commands.Cog.listener('on_button_click')
  async def click_handler(self, inter:disnake.MessageInteraction):
    if inter.data.custom_id == 'announce_send':
      await self.send_button_callback(inter)
    elif inter.data.custom_id == 'announce_resume':
      await self.resume_button_callback(inter)

  # Common functions

  def genstatus(
    self, message:str, subscribed:list, succeeded:int, failed:dict[str, list[str]]
  ) -> str:
    total = len(subscribed) - 1
    failedcount = sum((len(f) for f in failed.values()))
    failedstring = ''
    for k,v in failed.items():
      failedstring += f"{k}: {','.join(v)}\n"
    return (
      message + ' ' +
      f"{succeeded}/{total} sent, {failedcount} failed." +
      '\n' + self.bot.utilities.progress_bar(succeeded + failedcount, total, 30) +
      (
        '\n```\n' + self.bot.utilities.truncate(failedstring, 1800) + '\n```'
        if failed else ''
      )
    )

  async def send_announcement(
    self, msg:disnake.Message, skip=0, succeeded=0, failed:dict[str, list[str]] = {}
  ):
    """
      Sends / resumes sending an announcement to all subscribed users.
      Assumes the message has an embed and sends that as the announcement.
    """
    self.lock = True

    # Save this announcement to config so it can be resumed after a restart
    self.config['in_progress'] = f'{msg.channel.id}/{msg.id}'
    self.bot.config.save()

    subscribed = self.config['dm_subscription'].split(',')
    for encoded_uid in subscribed[skip:]:
      if encoded_uid == '':
        continue
      uid = decode_uid(encoded_uid)
      if uid is None:
        failed = add_to_failed(failed, 'Failed to decode user id', encoded_uid)
        continue
      await asyncio.sleep(0.4)
      try:
        if (succeeded + sum((len(f) for f in failed.values()))) % 5 == 0:
          await msg.edit(self.genstatus("Sending announcement...", subscribed, succeeded, failed))
        try:
          user = await self.bot.fetch_user(int(uid))
        except disnake.NotFound:
          failed = add_to_failed(failed, 'User not found', encoded_uid)
          continue
        try:
          await user.send(embed=msg.embeds[0])
        except disnake.Forbidden:
          failed = add_to_failed(failed, 'DM permission denied, unsubscribing user', encoded_uid)
          self.unsubscribe(user.id)
          self.bot.config.save()
          continue
        except disnake.DiscordServerError:
          failed = add_to_failed(failed, 'Server disconnect', encoded_uid)
          await asyncio.sleep(5)
          continue
        except disnake.HTTPException as e:
          if e.status == 400:
            failed = add_to_failed(
              failed, 'HTTP Exception 400 - Bad Request, unsubscribing user', encoded_uid
            )
            self.unsubscribe(user.id)
            self.bot.config.save()
            continue
          if e.status == 503:
            failed = add_to_failed(failed, 'HTTP Exception 503 - Service unavailable', encoded_uid)
            continue
          failed = add_to_failed(failed, '.status} - Unknown error', encoded_uid)
          continue
      except Exception as e:
        failed = add_to_failed(failed, f'Unhandled exception {e}', encoded_uid)
        continue
      succeeded += 1

    await msg.edit(self.genstatus("Announcement sent!", subscribed, succeeded, failed))
    self.config['in_progress'] = ''
    self.bot.config.save()

    self.lock = False

  # Modals

  class AnnounceModal(disnake.ui.Modal):
    """ Type out and send an announcement """
    def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
      """ Shorthand for self.bot.babel(scope, key, **values) """
      # this modal uses the new system scope
      return self.parent.bot.babel(target, self.parent.SCOPE, key, **values)

    def __init__(self, parent:Announce, inter:disnake.CommandInteraction):
      self.parent = parent

      super().__init__(
        title=self.babel(inter, 'announce_title'),
        components=[
          disnake.ui.TextInput(
            label=self.babel(inter, 'announce_title_of'),
            custom_id='title',
            style=disnake.TextInputStyle.single_line,
            min_length=1
          ),
          disnake.ui.TextInput(
            label=self.babel(inter, 'announce_content'),
            custom_id='content',
            style=disnake.TextInputStyle.long,
            min_length=1
          ),
          disnake.ui.TextInput(
            label=self.babel(inter, 'announce_url'),
            custom_id='url',
            style=disnake.TextInputStyle.single_line,
            min_length=0,
            required=False
          ),
          disnake.ui.TextInput(
            label=self.babel(inter, 'announce_image'),
            custom_id='image_url',
            style=disnake.TextInputStyle.single_line,
            min_length=0,
            required=False
          )
        ],
        timeout=600
      )

    async def callback(self, inter:disnake.ModalInteraction):
      embed = disnake.Embed(
        title=inter.text_values['title'],
        description=inter.text_values['content'],
        url=inter.text_values['url'],
        color=int(self.parent.bot.config['main']['themecolor'], 16)
      )
      embed.set_image(inter.text_values['image_url'])
      embed.set_footer(text=self.babel(inter, 'announce_unsubscribe_info'))

      subscribed = self.parent.config['dm_subscription'].split(',')
      buttons:list[disnake.Button] = [
        self.parent.SendButton(), self.parent.ResumeButton()
      ]
      buttons[1].disabled = True
      await inter.response.send_message(
        f"Announcement preview; (will be sent to {len(subscribed) - 1} users)",
        embed=embed,
        components=buttons
      )

  # Components

  class SendButton(disnake.ui.Button):
    def __init__(self):
      super().__init__(
        label='Send announcement',
        emoji='📨',
        custom_id='announce_send',
        style=disnake.ButtonStyle.green
      )

  async def send_button_callback(self, inter:disnake.MessageInteraction):
    if self.lock:
      # Lock means an announcement is already in progress
      return
    # Prevent any random users from pressing the button
    self.bot.auth.superusers(inter)

    # Disable button
    buttons:list[disnake.Button] = [self.SendButton(), self.ResumeButton()]
    buttons[0].disabled = True
    buttons[1].disabled = True
    await inter.response.edit_message(components=buttons)
    await self.send_announcement(await inter.original_message())

  class ResumeButton(disnake.ui.Button):
    def __init__(self):
      super().__init__(label='Resume sending', emoji='▶️', custom_id='announce_resume')

  async def resume_button_callback(self, inter:disnake.MessageInteraction):
    if self.lock:
      # Lock means an announcement is already in progress
      return
    # Prevent any random users from pressing the button
    self.bot.auth.superusers(inter)

    # Disable resume button once again
    buttons:list[disnake.Button] = [self.SendButton(), self.ResumeButton()]
    buttons[0].disabled = True
    buttons[1].disabled = True
    await inter.response.edit_message(components=buttons)

    # Recover state from message content
    succeeded = int(inter.message.content[24:].split('/')[0])
    failed = {}
    readnext = False
    for line in inter.message.content.splitlines():
      if line == '```':
        if readnext is False:
          readnext = True
        else:
          break
      elif readnext and line:
        if ':' not in line:
          raise Exception("Expected to find : in the following line;", line)
        fparts = line.split(':')
        if fparts[0] in failed:
          failed[fparts[0]] += fparts[1].split(',')
          continue
        failed[fparts[0]] = fparts[1].split(',')

    # Use recovered state to resume the announcement
    await self.send_announcement(
      inter.message, succeeded + sum((len(f) for f in failed.values())), succeeded, failed
    )

  # Commands

  @commands.bot_has_permissions(read_messages=True, send_messages=True)
  @commands.guild_only()
  @commands.default_member_permissions(administrator=True)
  @commands.slash_command()
  async def announce(self, inter:disnake.CommandInteraction):
    """ Sends an announcement to server owners and other subscribed users """
    await inter.response.send_modal(self.AnnounceModal(self, inter))


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(Announce(bot))
