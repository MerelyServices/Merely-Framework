"""
  Premium - exclusive functionality for paying users
  Prevents usage of an entire command unless a user has a certain role
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

from main import MerelyCog

if TYPE_CHECKING:
  from main import MerelyBot


class Premium(MerelyCog):
  """ Commands can be restricted to premium in the config, this extension enforces it """
  SCOPE = 'premium'

  premiumguild: discord.Guild
  premiumroles: set[discord.Role]
  owner_paid_flag: bool

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
    if 'custom_bot_owner' not in self.config:
      self.config['custom_bot_owner'] = ''

    if not self.config['premium_role_guild'] or not self.config['premium_roles']:
      raise Exception("Premium needs premium_role_guild and premium_roles set in config!")
    if not bot.config.get('help', 'serverinv', fallback=''):
      raise Exception("Premium needs serverinv to be set in config!")

    self.premiumroles = set()
    self.owner_paid_flag = True

    # Add command checker
    self.original_interaction_check = self.bot.tree.interaction_check
    self.bot.tree.interaction_check = self.check_premium_slash_command

  def cog_unload(self):
    # Revert checker to default
    self.bot.tree.interaction_check = self.original_interaction_check

  # Event listeners

  @commands.Cog.listener('on_connect')
  async def on_connect(self):
    """ Fetches guild and member list on connect, checks if the owner has paid their bill """
    await asyncio.sleep(5)
    _premiumguild = self.bot.get_guild(int(self.config['premium_role_guild']))
    if not _premiumguild:
      if not self.bot.quiet:
        print("Note: had to fetch premium guild as it has not been loaded yet")
      self.premiumguild = await self.bot.fetch_guild(int(self.config['premium_role_guild']))
    else:
      self.premiumguild = _premiumguild

    # Set a flag if this is a custom bot and the owner doesn't have the premium role
    if self.config.get('custom_bot_owner'):
      if ownerid := self.config.getint('custom_bot_owner'):
        self.owner_paid_flag = False
        if owner := self.bot.get_user(ownerid):
          if self.check_premium(owner):
            self.owner_paid_flag = True
        if not self.owner_paid_flag:
          print("ALERT: This bot has been disabled because the owner doesn't appear to have premium")

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
    """ Checks all commands to block in the event of missing premium, if required """
    if inter.type != discord.InteractionType.application_command:
      return True

    if not self.owner_paid_flag:
      # The owner hasn't paid for premium, refuse to work
      print(inter.command, inter.command.module if inter.command else 'No module')
      if inter.command and inter.command.module == 'extensions.system':
        # System commands must continue to function
        return True
      await inter.response.send_message(embed=self.error_embed(inter, True), ephemeral=True)
      return False

    restricted = self.config['restricted_commands'].split(' ')
    premium_users = [int(u) for u in self.config['premium_users'].split(' ') if u]
    assert inter.command is not None
    if inter.command.name in restricted:
      if inter.user.id in premium_users:
        return True # user is automatically premium through config
      if await self.check_premium(inter.user):
        return True # user is premium
      await inter.response.send_message(embed=self.error_embed(inter), ephemeral=True)
      return False # user is not premium
    return True # command is not restricted

  def error_embed(self, inter:discord.Interaction, owner=False) -> discord.Embed:
    rolelist = self.bot.babel.string_list(inter, [r.name for r in self.premiumroles], True)
    embed = discord.Embed(
      title=self.babel(inter, 'required_title'),
      description=self.babel(inter, 'owner_required_error' if owner else 'required_error')
    )
    embed.url = (
      self.config['patreon'] if self.config['patreon']
      else self.config['other']
    )
    embed.set_thumbnail(url=self.config['icon'])
    embed.set_footer(
      text=self.babel(inter, 'owner_required_advice' if owner else 'required_advice', role=rolelist)
    )
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

  @app_commands.command(
    name=app_commands.locale_str('premium', scope=SCOPE),
    description=app_commands.locale_str('premium_desc', scope=SCOPE)
  )
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

    kwargs: dict
    kwargs = {'view': self.PremiumView(inter, self)} if self.bot.config['help']['serverinv'] else {}
    await inter.response.send_message(
      embed=embed,
      **kwargs
    )


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Premium(bot))
