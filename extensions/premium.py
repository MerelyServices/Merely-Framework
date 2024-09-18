"""
  Premium - exclusive functionality for paying users
  Still rather primitive, prevents usage of an entire command unless a user has a certain role
  Currently unused until new premium exclusive features are developed
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


class Premium(commands.Cog):
  """ Commands can be restricted to premium in the config, this extension enforces it """
  SCOPE = 'premium'

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  premiumguild: discord.Guild
  premiumroles: set[discord.Role]

  def __init__(self, bot:MerelyBot):
    self.bot = bot

    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)
    if 'icon' not in self.config:
      self.config['icon'] = ''
    if 'patreon' not in self.config:
      self.config['patreon'] = ''
    if 'other' not in self.config:
      self.config['other'] = ''
    if 'restricted_commands' not in self.config:
      self.config['restricted_commands'] = ''
    if 'restricted_config' not in self.config:
      self.config['restricted_config'] = ''
    if 'premium_role_guild' not in self.config or\
       not self.config['premium_role_guild'] or\
       'premium_roles' not in self.config or\
       not self.config['premium_roles']:
      self.config['premium_role_guild'] = ''
      self.config['premium_roles'] = ''
      bot.config.save()
    if 'premium_users' not in self.config:
      self.config['premium_users'] = ''
    if 'offer_custom_bot' not in self.config:
      self.config['offer_custom_bot'] = 'False'

    if not self.config['premium_role_guild'] or not self.config['premium_roles']:
      raise Exception("Premium needs premium_role_guild and premium_roles set in config!")
    if not bot.config.get('help', 'serverinv', fallback=''):
      raise Exception("Premium needs serverinv to be set in config!")

    self.premiumguild = None
    self.premiumroles = set()

    # Add command checker
    self.original_interaction_check = self.bot.tree.interaction_check
    self.bot.tree.interaction_check = self.check_premium_slash_command

  def cog_unload(self):
    # Revert checker to default
    self.bot.tree.interaction_check = self.original_interaction_check

  # Event listeners

  @commands.Cog.listener('on_connect')
  async def cache_role(self):
    """ Fetches guild and member list on connect to decrease first response time """
    await asyncio.sleep(5)
    self.premiumguild = self.bot.get_guild(int(self.config['premium_role_guild']))
    if not self.premiumguild:
      if not self.bot.quiet:
        print("Note: had to fetch premium guild as it has not been loaded yet")
      self.premiumguild = await self.bot.fetch_guild(int(self.config['premium_role_guild']))

    # Repopulate list of premium roles
    self.premiumroles = set()
    targets = self.config['premium_roles'].split(' ')
    for role in await self.premiumguild.fetch_roles():
      if str(role.id) in targets:
        self.premiumroles.add(role)

    if not self.premiumroles:
      raise Exception("The designated premium role was not found!")

  # Utils

  async def check_premium(self, user:discord.User | discord.Member):
    try:
      member = await self.premiumguild.fetch_member(user.id)
    except discord.NotFound:
      return False
    else:
      return list(self.premiumroles & set(member.roles))

  # Checks

  async def check_premium_slash_command(self, inter:discord.Interaction) -> bool:
    #TODO: maybe check other interaction types too?
    if inter.type != discord.InteractionType.application_command:
      return True

    restricted = self.config['restricted_commands'].split(' ')
    premium_users = [int(u) for u in self.config['premium_users'].split(' ') if u]
    if inter.command.name in restricted:
      if inter.user.id in premium_users:
        return True # user is automatically premium through config
      if await self.check_premium(inter.user):
        return True # user is premium
      await inter.response.send_message(embed=self.error_embed(inter), ephemeral=True)
      return False # user is not premium
    return True # command is not restricted

  def error_embed(self, inter:discord.Interaction) -> discord.Embed:
    rolelist = self.bot.babel.string_list(inter, [r.name for r in self.premiumroles], True)
    embed = discord.Embed(
      title=self.babel(inter, 'required_title'),
      description=self.babel(inter, 'required_error')
    )
    embed.url = (
      self.config['patreon'] if self.config['patreon']
      else self.config['other']
    )
    embed.set_thumbnail(url=self.config['icon'])
    embed.set_footer(text=self.babel(inter, 'required_advice', role=rolelist))
    return embed

  # Views

  class PremiumView(discord.ui.View):
    def __init__(self, inter:discord.Interaction, parent:Premium):
      super().__init__(timeout=None)

      url = None
      if parent.config['patreon'] or parent.config['other']:
        url = (
          parent.config['patreon'] if parent.config['patreon']
          else parent.config['other']
        )

      self.add_item(discord.ui.Button(
        emoji='1️⃣',
        label=parent.babel(inter, 'join_server_cta'),
        url=parent.bot.config['help']['serverinv']
      ))
      self.add_item(discord.ui.Button(
        emoji='2️⃣',
        label=parent.babel(inter, 'subscribe_cta'),
        url=url
      ))

  # Commands

  @app_commands.command()
  async def premium(self, inter:discord.Interaction):
    """
      Learn more about premium.
    """
    fulldesc = self.babel(inter, 'desc')
    #BABEL: feature_#,feature_#_desc
    i = 1
    while f'feature_{i}' in self.bot.babel.langs[self.bot.babel.baselang][self.SCOPE]:
      if self.babel(inter, f'feature_{i}') == '':
        i += 1
        continue
      fulldesc += '\n### ' + self.babel(inter, f'feature_{i}')
      fulldesc += '\n' + self.babel(inter, f'feature_{i}_desc')
      i += 1
    if self.config.getboolean('offer_custom_bot', False):
      fulldesc += '\n### ' + self.babel(inter, 'feature_custom')
      fulldesc += '\n' + self.babel(inter, 'feature_custom_desc')

    embed = discord.Embed(title=self.babel(inter, 'name'), description=fulldesc)

    if self.config['patreon'] or self.config['other']:
      embed.url = (
        self.config['patreon'] if self.config['patreon']
        else self.config['other']
      )
    if self.config['icon']:
      embed.set_thumbnail(url=self.config['icon'])
    embed.set_footer(text=self.babel(inter, 'fine_print'))

    await inter.response.send_message(
      embed=embed,
      view=self.PremiumView(inter, self) if self.bot.config['help']['serverinv'] else None
    )


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Premium(bot))
