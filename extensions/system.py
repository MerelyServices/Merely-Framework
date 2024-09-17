"""
  System - Bot management commands
  Dependencies: Auth
"""

from __future__ import annotations

from enum import Enum
import asyncio, io, os, re, importlib, glob, contextlib
from typing import Optional, TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

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

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    # for legacy reasons, this module has no local scope
    #BABEL: -main
    return self.bot.babel(target, 'main', key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot

    # Restrict usage of these commands to specified guilds
    if bot.config['auth']['botadmin_guilds']:
      guilds = bot.config['auth']['botadmin_guilds']
      botadmin_guilds = [int(guild) for guild in guilds.split(' ')]
      for cmd in self.get_app_commands():
        cmd._guild_ids = botadmin_guilds
    elif not bot.quiet:
      print("  WARN: No botadmin_guilds defined, so all servers will be able to see system commands!")

  # Commands

  @app_commands.command()
  @app_commands.default_permissions(administrator=True)
  @app_commands.guild_only()
  async def module(self, inter:discord.Interaction, action:Actions, module:Optional[str] = None):
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
      await inter.response.send_message(
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
          raise AssertionError(f"Unhandled special module {module}!")

        await inter.response.send_message(
          self.babel(inter, 'extension_reload_success', extension=module),
          ephemeral=True
        )
        return

      if action == Actions.load:
        base_ext_files = glob.glob(os.path.join('extensions', '*.py'))
        ovl_ext_files = glob.glob(
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
          await inter.response.send_message(
            self.babel(inter, 'extension_enable_success', extension=module),
            ephemeral=True
          )
        elif action == Actions.disable:
          self.bot.config['extensions'][module] = 'False'
          self.bot.config.save()
          await inter.response.send_message(
            self.babel(inter, 'extension_disable_success', extension=module),
            ephemeral=True
          )
        elif action == Actions.load:
          await self.bot.load_extension(module_match)
          await inter.response.send_message(
            self.babel(inter, 'extension_load_success', extension=module),
            ephemeral=True
          )
          await self.bot.sync_commands()
        elif action == Actions.unload:
          await self.bot.unload_extension(module_match)
          await inter.response.send_message(
            self.babel(inter, 'extension_unload_success', extension=module),
            ephemeral=True
          )
          await self.bot.sync_commands()
        elif action == Actions.reload:
          await self.bot.reload_extension(module_match)
          await inter.response.send_message(
            self.babel(inter, 'extension_reload_success', extension=module),
            ephemeral=True
          )
          await self.bot.sync_commands()
        else:
          raise commands.BadArgument()
        cogmodules = {cog.lower().replace('_', ''): cog for cog in self.bot.cogs}
        compatmod = module.lower().replace('_', '')
        if compatmod in cogmodules:
          # Fire ready events again in the loaded module
          for listener in self.bot.cogs[cogmodules[compatmod]].get_listeners():
            if listener[0] == 'on_connect':
              if self.bot.verbose:
                print("Firing event", listener[1].__name__, "as a part of loading module", module)
              asyncio.ensure_future(listener[1]())
            elif listener[0] == 'on_ready' and self.bot.is_ready():
              if self.bot.verbose:
                print("Firing event", listener[1].__name__, "as a part of loading module", module)
              asyncio.ensure_future(listener[1]())
      else:
        await inter.response.send_message(self.babel(inter, 'extension_file_missing'), ephemeral=True)
    else:
      await inter.response.send_message(self.babel(inter, 'extension_not_found'), ephemeral=True)

  @module.autocomplete('module')
  async def module_ac(self, inter:discord.Interaction, search:str) -> list[app_commands.Choice[str]]:
    """ Suggests modules based on the list in config """
    extension_list = None
    if 'action' in inter.data.get('options', {}):
      if inter.data.get('options').get('action').get('value') in [Actions.reload, Actions.unload]:
        extension_list = [
          e.replace('extensions.','').replace('overlay.','').strip('_')
          for e in self.bot.extensions.keys()
        ]
      elif inter['options']['action']['value'] == Actions.list:
        return []
    if extension_list is None:
      stock_extensions = glob.glob(os.path.join('extensions', '*.py'))
      overlay_extensions = (
        glob.glob(os.path.join('overlay', 'extensions', '*.py')) if self.bot.overlay else []
      )
      extension_list = list(set(
        re.sub(r'^(extensions[/\\]|overlay[/\\]extensions[/\\])', '', f).strip('_')[:-3]
        for f in (overlay_extensions + stock_extensions)
      ))
    return [
      app_commands.Choice(name=x, value=x) for x in extension_list + self.SPECIAL_MODULES
      if search in x
    ][:25]

  @app_commands.command()
  @app_commands.default_permissions(administrator=True)
  @app_commands.guild_only()
  async def migrate(self, inter:discord.Interaction, script:str):
    """
    Manually trigger a config migration script

    Parameters
    ----------
    script: The filename of the migration script you would like to trigger
    """
    self.bot.auth.superusers(inter)

    # For security, generate a list of approved scripts
    migrations:list[str] = []
    if os.path.exists('migrations'):
      migrations += glob.glob(os.path.join('migrations', 'v*_*.py'))
    if os.path.exists(os.path.join('overlay', 'migrations')):
      migrations += glob.glob(os.path.join('overlay', 'migrations', 'v*_*.py'))
    # Check script path is valid
    if script not in migrations:
      await inter.response.send_message(
        "Script not found! You can only choose a script from the autocomplete list."
      )
      return
    # Begin the migration
    module = importlib.import_module(re.sub(r'[/\\]', '.', script[:-3]), 'main')
    f = io.StringIO()
    try:
      with contextlib.redirect_stdout(f):
        module.migrate(self.bot.config)
    except Exception as e:
      await inter.response.send_message(f"Exception encountered while running migration;```{e}```")
    else:
      await inter.response.send_message(
        f"Migration succeeded with the following output;```{f.getvalue()}```"
      )
    self.bot.config.save()

  @migrate.autocomplete('script')
  async def migrate_ac(self, _:discord.Interaction, search:str) -> list[app_commands.Choice[str]]:
    """ Return a list of matching migration scripts """
    migrations:list[str] = []
    if os.path.exists('migrations'):
      migrations += glob.glob(os.path.join('migrations', 'v*_*.py'))
    if os.path.exists(os.path.join('overlay', 'migrations')):
      migrations += glob.glob(os.path.join('overlay', 'migrations', 'v*_*.py'))
    return [app_commands.Choice(name=m, value=m) for m in migrations if search in m]

  @app_commands.command()
  @app_commands.default_permissions(administrator=True)
  @app_commands.guild_only()
  async def delete_message(
    self, inter:discord.Interaction, channel_id:str, message_id:str
  ):
    """ Deletes a message """
    self.bot.auth.superusers(inter)

    try:
      channel = await self.bot.fetch_channel(int(channel_id))
      message = await channel.fetch_message(int(message_id))
    except TypeError:
      await inter.response.send_message("Provided ids are invalid!")
      return
    except discord.NotFound:
      await inter.response.send_message("Message/channel id does not match!")
      return

    try:
      await message.delete()
    except discord.Forbidden:
      await inter.response.send_message("Bot is missing permissions!")
      return

    await inter.response.send_message("Deleted message successfully!")

  @app_commands.command()
  @app_commands.default_permissions(administrator=True)
  @app_commands.guild_only()
  @commands.cooldown(1, 1)
  async def die(
    self, inter:discord.Interaction, saveconfig:bool = False, restart:bool = False
  ):
    """
    Log out and shut down

    Parameters
    ----------
    saveconfig: Write the last known state of the config file on shutdown
    """
    self.bot.auth.superusers(inter)

    await inter.response.send_message(self.bot.babel(inter, 'admin', 'die_success', restart=restart))
    if saveconfig:
      self.bot.config.save()
    self.bot.restart = restart
    await self.bot.close()


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(System(bot))
