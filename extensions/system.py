"""
  System - Bot management commands
  Dependencies: Auth
"""

from __future__ import annotations

from enum import Enum
from glob import glob
import asyncio, os, re
from typing import Optional, TYPE_CHECKING
import disnake
from disnake.ext import commands

if TYPE_CHECKING:
  from ..main import MerelyBot
  from ..babel import Resolvable


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
  SCOPE = 'main' # for legacy reasons, this module has no local scope

  @property
  def config(self) -> dict[str, str]:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    if not bot.config.getboolean('extensions', 'auth', fallback=False):
      raise Exception("'auth' must be enabled to use 'admin'")

    # Restrict usage of these commands to one guild
    guilds = bot.config['auth']['botadmin_guilds']
    botadmin_guilds = [int(guild) for guild in guilds.split(' ')]
    for cmd in self.get_application_commands():
      cmd.guild_ids = botadmin_guilds

  @commands.slash_command()
  @commands.default_member_permissions(administrator=True)
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

    self.bot.cogs['Auth'].superusers(inter)

    active_extensions = [
      re.sub(r'^(extensions\.|overlay\.extensions\.)', '', e).strip('_')
      for e in self.bot.extensions.keys()
    ] + ['config', 'babel']
    if module is None or action == Actions.list:
      await inter.send(
        self.babel(inter, 'extensions_list', list='\n'.join(active_extensions)),
        ephemeral=True
      )
      return

    if not self.bot.config.getboolean('extensions', 'allow_reloading'):
      await inter.send(self.babel('reloading_disabled'), ephemeral=True)
      return

    module = module.lower()
    module_match = None
    if module in active_extensions or action == Actions.load:
      if module == 'config':
        self.bot.config.reload()
        await inter.send(
          self.babel(inter, 'extension_reload_success', extension=module),
          ephemeral=True
        )
        return
      elif module == 'babel':
        self.bot.babel.load()
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
            elif listener[0] == 'on_ready':
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
          e.replace('extensions.','').strip('_') for e in self.bot.extensions.keys()
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
      [e for e in ['config', 'babel'] if search in e]
    )

  @commands.slash_command()
  async def delete_message(
    self,
    inter:disnake.CommandInteraction,
    channel_id:str,
    message_id:str
  ):
    """ Deletes a message """
    self.bot.cogs['Auth'].superusers(inter)

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

  @commands.slash_command()
  @commands.cooldown(1, 1)
  async def die(self, inter:disnake.CommandInteraction, saveconfig:bool = False):
    """
    Log out and shut down

    Parameters
    ----------
    saveconfig: Write the last known state of the config file on shutdown
    """
    self.bot.cogs['Auth'].superusers(inter)
    await inter.send(self.bot.babel(inter, 'admin', 'die_success'))
    if saveconfig:
      self.bot.config.save()
    await self.bot.close()


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(System(bot))
