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


class Announce(commands.Cog):
  """ Handles DM announcements and ensures the process can resume after a crash or restart """
  SCOPE = 'announce'
  lock = False

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
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
    guilds = bot.config['auth']['botadmin_guilds']
    botadmin_guilds = [int(guild) for guild in guilds.split(' ')]
    for cmd in self.get_application_commands():
      cmd.guild_ids = botadmin_guilds

  def controlpanel_settings(self, inter:disnake.Interaction):
    # ControlPanel integration
    return [
      Listable(self.SCOPE, 'dm_subscription', 'dm_subscription', self.encode_uid(inter.user.id))
    ]

  def controlpanel_theme(self) -> tuple[str, disnake.ButtonStyle]:
    # Controlpanel custom theme for buttons
    return (self.SCOPE, disnake.ButtonStyle.red)

  # Events

  async def cog_load(self):
    # Inform bot of unsent announcements, ongoing announcements are handled in on_ready
    self.bot.add_view(self.AnnounceView(self))
    print(list(view for view in self.bot.persistent_views))

  def subscribe(self, user:disnake.User) -> int:
    # Subscribes users if they have never been subscribed before
    uid = self.encode_uid(user.id)
    if (
      user
      and f'{uid},' not in self.config['subscription_history']
      and f'{uid},' not in self.config['dm_subscription']
    ):
      self.config['dm_subscription'] += f'{uid},'
      self.config['subscription_history'] += f'{uid},'
      return 1
    return 0

  @commands.Cog.listener('on_ready')
  async def catchup(self):
    await asyncio.sleep(15) # Wait to reduce flood of commands on connect

    # Enable resume button if an announcement was in progress
    if self.config['in_progress']:
      raw_channel_id, raw_message_id = self.config['in_progress'].split('/')
      channel = self.bot.get_channel(int(raw_channel_id))
      msg = await channel.fetch_message(int(raw_message_id))
      view = self.AnnounceView(self, resume=True)
      await msg.edit(view=view)

    print("Searching for server owners...")
    count = 0
    for guild in self.bot.guilds:
      if guild.owner_id:
        member = await guild.fetch_member(guild.owner_id)
        count += self.subscribe(member)
    print("Finished searching for server owners.", count, "added.")
    self.bot.config.save()

  @commands.Cog.listener('on_guild_join')
  async def autosubscribe(self, guild:disnake.Guild):
    self.subscribe(guild.owner)
    self.bot.config.save()

  # Common functions

  def encode_uid(self, uid:int) -> str:
    return base64.b64encode(uid.to_bytes(8, 'big')).decode('ascii').replace('=','')

  def decode_uid(self, uid:str) -> int | None:
    if len(uid) == 11:
      uid += '='
    try:
      return int.from_bytes(base64.b64decode(uid), 'big')
    except Exception:
      print(f"WARN: {uid} is not a valid encoded UID.")
      return None

  def genstatus(self, message:str, subscribed:list, succeeded:int, failed:list[str]) -> str:
    total = len(subscribed) - 1
    return (
      message + ' ' +
      f"{succeeded}/{total} sent, {len(failed)} failed." +
      '\n' + self.bot.utilities.progress_bar(succeeded, total - len(failed), 40) +
      (
        '\n```\n' + self.bot.utilities.truncate('\n'.join(failed), 1800) + '\n```'
        if failed else ''
      )
    )

  async def send_announcement(self, msg:disnake.Message, skip=0, succeeded=0, failed:list[str] = []):
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
      uid = self.decode_uid(encoded_uid)
      if uid is None:
        failed.append(f'{encoded_uid} - Failed to decode user id')
        continue
      await asyncio.sleep(0.4)
      try:
        if (succeeded + len(failed)) % 5 == 0:
          await msg.edit(self.genstatus("Sending announcement...", subscribed, succeeded, failed))
        try:
          user = await self.bot.fetch_user(int(uid))
        except disnake.NotFound:
          failed.append(f'{encoded_uid} - User not found')
          continue
        try:
          # simulate sending messages by still firing a coroutine
          await user.trigger_typing() # .send(embed=msg.embed)
        except disnake.Forbidden:
          failed.append(f'{encoded_uid} - DM permission denied')
          continue
        except disnake.DiscordServerError:
          failed.append(f'{encoded_uid} - Server disconnect')
          await asyncio.sleep(5)
          continue
      except Exception as e:
        failed.append(f'{encoded_uid} - Unhandled exception {e}')
        continue
      succeeded += 1

    await msg.edit(self.genstatus("Announcement sent!", subscribed, succeeded, failed))
    self.config['in_progress'] = ''
    self.bot.config.save()

    self.lock = False

  # Modals

  class AnnounceModal(disnake.ui.Modal):
    """ Type out and send an announcement """
    def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
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
      view = self.parent.AnnounceView(self.parent)
      await inter.response.send_message(
        f"Announcement preview; (will be sent to {len(subscribed) - 1} users)",
        embed=embed,
        view=view
      )

  # Views

  class AnnounceView(disnake.ui.View):
    def __init__(self, parent:Announce, *, resume=False):
      self.parent = parent
      super().__init__(timeout=None)
      self.send_button.disabled = resume
      self.resume_button.disabled = not resume

    @disnake.ui.button(
      label='Send announcement',
      emoji='✈️', style=disnake.ButtonStyle.green,
      custom_id='announce_send'
    )
    async def send_button(self, _:disnake.Button, inter:disnake.MessageInteraction):
      # Prevent any random users from pressing the button
      self.parent.bot.auth.superusers(inter)

      # Disable button to prevent double firing
      self.send_button.disabled = True
      await inter.response.edit_message(view=self)
      await self.parent.send_announcement(await inter.original_message())

    @disnake.ui.button(label='Resume sending', emoji='▶️', custom_id='announce_resume')
    async def resume_button(self, _:disnake.Button, inter:disnake.MessageInteraction):
      if self.parent.lock:
        # Lock means an announcement is already in progress
        return

      # Disable resume button once again
      self.resume_button.disabled = True
      await inter.response.edit_message(view=self)

      # Recover state from message content
      succeeded = int(inter.message.content[24:].split('/')[0])
      failed = []
      readnext = False
      for line in inter.message.content.splitlines():
        if line == '```':
          if readnext is False:
            readnext = True
          else:
            break
        if readnext:
          failed.append(line)

      # Use recovered state to resume the announcement
      await self.parent.send_announcement(
        inter.message, succeeded + len(failed), succeeded, failed
      )

  # Commands

  @commands.guild_only()
  @commands.default_member_permissions(administrator=True)
  @commands.slash_command()
  async def announce(self, inter:disnake.CommandInteraction):
    """ Sends an announcement to server owners and other subscribed users """
    await inter.response.send_modal(self.AnnounceModal(self, inter))


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(Announce(bot))
