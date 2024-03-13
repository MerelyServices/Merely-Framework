"""
  System - Bot management commands
  Dependencies: Auth
"""

from __future__ import annotations

from enum import Enum
from glob import glob
import asyncio, os, re, importlib
from typing import Optional, TYPE_CHECKING
import disnake
from disnake.ext import commands

from extensions.controlpanel import Listable

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


class Actions(int, Enum):
  """ Actions that can be performed on an option """
  list = 0
  load = 1
  unload = 2
  reload = 3
  enable = 4
  disable = 5


class System(commands.Cog):
  """commands involved in working with a discord bot"""
  SCOPE = 'system'
  SPECIAL_MODULES = ['config', 'babel', 'utilities', 'auth']

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    # for legacy reasons, this module has no local scope
    #BABEL: -main
    return self.bot.babel(target, 'main', key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot

    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)
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
      Listable(self.SCOPE, 'dm_subscription', 'dm_subscription', str(inter.user.id))
    ]

  def controlpanel_theme(self) -> tuple[str, disnake.ButtonStyle]:
    # Controlpanel custom theme for buttons
    return (self.SCOPE, disnake.ButtonStyle.red)

  # Modals

  class AnnounceModal(disnake.ui.Modal):
    """ Type out and send an announcement """
    def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
      """ Shorthand for self.bot.babel(scope, key, **values) """
      # this modal uses the new system scope
      return self.parent.bot.babel(target, self.parent.SCOPE, key, **values)

    def __init__(self, parent:System, inter:disnake.CommandInteraction, testing:bool):
      self.parent = parent
      self.testing = testing

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
        timeout=300
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

      await inter.response.defer(ephemeral=True)
      subscribed = self.parent.config['dm_subscription'].split(',')
      if self.testing:
        await inter.followup.send(
          f"Announcement preview; (will be sent to {len(subscribed)} users)",
          embed=embed,
          ephemeral=True
        )
        return
      for uid in subscribed:
        if uid == '':
          continue
        try:
          user = await self.parent.bot.fetch_user(int(uid))
        except disnake.NotFound:
          continue
        try:
          await user.send(embed=embed)
        except disnake.Forbidden:
          continue
      await inter.followup.send("Your announcement has been sent", ephemeral=True)

  # Events

  def subscribe(self, user:disnake.User) -> int:
    # Subscribes users if they have never been subscribed before
    if (
      user
      and f'{user.id},' not in self.config['subscription_history']
      and f'{user.id},' not in self.config['dm_subscription']
    ):
      self.config['dm_subscription'] += f'{user.id},'
      self.config['subscription_history'] += f'{user.id},'
      return 1
    return 0

  @commands.Cog.listener('on_ready')
  async def search_and_subscribe(self):
    await asyncio.sleep(15) # Wait to reduce flood of commands on connect
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

  # Commands

  @commands.default_member_permissions(administrator=True)
  @commands.slash_command()
  async def module(
    self,
    inter:disnake.CommandInteraction,
    action:Actions,
    module:Optional[str] = None
  ):
    """
    Manage modules of the bot in real time

    Parameters
    ----------
    action: The action you want to perform
    module: The target cog which will be affected, leave empty for a list of loaded Cogs
    """

    self.bot.auth.superusers(inter)

    active_extensions = [
      re.sub(r'^(extensions\.|overlay\.extensions\.)', '', e).strip('_')
      for e in self.bot.extensions.keys()
    ] + self.SPECIAL_MODULES
    if module is None or action == Actions.list:
      await inter.send(
        self.babel(inter, 'extensions_list', list='\n'.join(active_extensions)),
        ephemeral=True
      )
      return

    module = module.lower()
    module_match = None
    if module in active_extensions or action == Actions.load:
      if module in self.SPECIAL_MODULES:
        if module == 'config':
          self.bot.config.reload()
        elif module == 'babel':
          self.bot.babel.load()
        elif module == 'utilities':
          self.bot.utilities = importlib.import_module('utilities', 'main').Utilities()
        elif module == 'auth':
          self.bot.auth = importlib.import_module('auth', 'main').Auth(self.bot)
        else:
          raise AssertionError(f"Unhanlded special module {module}!")

        await inter.send(
          self.babel(inter, 'extension_reload_success', extension=module),
          ephemeral=True
        )
        return

      if action == Actions.load:
        base_ext_files = glob(os.path.join('extensions', '*.py'))
        ovl_ext_files = glob(
          os.path.join('overlay', 'extensions', '*.py')
        ) if self.bot.overlay else []
        # Prioritise overlay extensions over built-in extensions
        for f in ovl_ext_files + base_ext_files:
          if (
            re.sub(r'^(extensions[/\\]|overlay[/\\]extensions[/\\])', '', f).strip('_')[:-3] == module
          ):
            module_match = f[:-3].replace(os.path.sep,'.')
            break
      else:
        module_candidate = [
          ext for ext in self.bot.extensions.keys()
          if re.sub(r'^(extensions\.|overlay\.extensions\.)', '', ext).strip('_') == module
        ]
        if module_candidate:
          module_match = module_candidate[0]

      if module_match:
        if action == Actions.enable:
          self.bot.config['extensions'][module] = 'True'
          self.bot.config.save()
          await inter.send(
            self.babel(inter, 'extension_enable_success', extension=module),
            ephemeral=True
          )
        elif action == Actions.disable:
          self.bot.config['extensions'][module] = 'False'
          self.bot.config.save()
          await inter.send(
            self.babel(inter, 'extension_disable_success', extension=module),
            ephemeral=True
          )
        elif action == Actions.load:
          self.bot.load_extension(module_match)
          await inter.send(
            self.babel(inter, 'extension_load_success', extension=module),
            ephemeral=True
          )
        elif action == Actions.unload:
          self.bot.unload_extension(module_match)
          await inter.send(
            self.babel(inter, 'extension_unload_success', extension=module),
            ephemeral=True
          )
        elif action == Actions.reload:
          self.bot.reload_extension(module_match)
          await inter.send(
            self.babel(inter, 'extension_reload_success', extension=module),
            ephemeral=True
          )
        else:
          raise commands.BadArgument
        cogmodules = {cog.lower(): cog for cog in self.bot.cogs}
        if module in cogmodules:
          for listener in self.bot.cogs[cogmodules[module]].get_listeners():
            if listener[0] == 'on_connect':
              asyncio.ensure_future(listener[1]())
            elif listener[0] == 'on_ready' and self.bot.is_ready():
              asyncio.ensure_future(listener[1]())
      else:
        await inter.send(self.babel(inter, 'extension_file_missing'), ephemeral=True)
    else:
      await inter.send(self.babel(inter, 'extension_not_found'), ephemeral=True)

  @module.autocomplete('module')
  async def module_ac(self, inter:disnake.CommandInteraction, search:str):
    """ Suggests modules based on the list in config """
    extension_list = None
    if 'action' in inter.filled_options:
      if inter.filled_options['action'] in [Actions.reload, Actions.unload]:
        extension_list = (
          e.replace('extensions.','').replace('overlay.','').strip('_')
          for e in self.bot.extensions.keys()
        )
      elif inter.filled_options['action'] == Actions.list:
        return []
    if extension_list is None:
      stock_extensions = glob(os.path.join('extensions', '*.py'))
      overlay_extensions = (
        glob(os.path.join('overlay', 'extensions', '*.py')) if self.bot.overlay else []
      )
      extension_list = set(
        re.sub(r'^(extensions[/\\]|overlay[/\\]extensions[/\\])', '', f).strip('_')[:-3]
        for f in (overlay_extensions + stock_extensions)
      )
    return (
      [x for x in extension_list if search in x] +
      [e for e in self.SPECIAL_MODULES if search in e]
    )

  @commands.guild_only()
  @commands.default_member_permissions(administrator=True)
  @commands.slash_command()
  async def announce(self, inter:disnake.CommandInteraction, testing:bool = False):
    """ Sends an announcement to server owners and other subscribed users """
    await inter.response.send_modal(self.AnnounceModal(self, inter, testing))

  @commands.default_member_permissions(administrator=True)
  @commands.slash_command()
  async def delete_message(
    self, inter:disnake.CommandInteraction, channel_id:str, message_id:str
  ):
    """ Deletes a message """
    self.bot.auth.superusers(inter)

    try:
      channel = await self.bot.fetch_channel(int(channel_id))
      message = await channel.fetch_message(int(message_id))
    except TypeError:
      await inter.send("Provided ids are invalid!")
      return
    except disnake.NotFound:
      await inter.send("Message/channel id does not match!")
      return

    try:
      await message.delete()
    except disnake.Forbidden:
      await inter.send("Bot is missing permissions!")
      return

    await inter.send("Deleted message successfully!")

  @commands.default_member_permissions(administrator=True)
  @commands.slash_command()
  @commands.cooldown(1, 1)
  async def die(self, inter:disnake.CommandInteraction, saveconfig:bool = False):
    """
    Log out and shut down

    Parameters
    ----------
    saveconfig: Write the last known state of the config file on shutdown
    """
    self.bot.auth.superusers(inter)
    await inter.send(self.bot.babel(inter, 'admin', 'die_success'))
    if saveconfig:
      self.bot.config.save()
    await self.bot.close()


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(System(bot))
