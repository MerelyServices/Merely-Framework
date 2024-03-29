"""
  Premium - exclusive functionality for paying users
  Still rather primitive, prevents usage of an entire command unless a user has a certain role
  Currently unused until new premium exclusive features are developed
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
import disnake
from disnake.ext import commands

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

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  premiumguild: disnake.Guild
  premiumroles: list[disnake.Role]

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

    self.premiumguild = None
    self.premiumroles = []

    bot.add_app_command_check(
      self.check_premium_slash_command, slash_commands=True, user_commands=True
    )

  async def cog_load(self):
    if not (self.config['premium_role_guild'] or self.config['premium_roles']):
      raise Exception(
        "You must provide a reference to a guild and at least one role in order for premium to work!"
      )
    if not self.bot.config.get('help', 'serverinv', fallback=''):
      self.bot.config.save()
      raise Exception(
        "You must have an invite to the support server with the supporter role in " +
        "config[help][serverinv]!"
      )

  @commands.Cog.listener('on_connect')
  async def cache_role(self):
    """ Fetches guild and member list on connect to decrease first response time """
    await asyncio.sleep(5)
    self.premiumguild = self.bot.get_guild(int(self.config['premium_role_guild']))
    if not self.premiumguild:
      print("Note: had to fetch premium guild as it has not been loaded yet")
      self.premiumguild = await self.bot.fetch_guild(int(self.config['premium_role_guild']))
    targets = self.config['premium_roles'].split(' ')
    for role in await self.premiumguild.fetch_roles():
      if str(role.id) in targets:
        self.premiumroles.append(role)

    if not self.premiumroles:
      raise Exception("The designated premium role was not found!")

  async def check_premium(self, user:disnake.User):
    member = await self.premiumguild.fetch_member(user.id)
    if isinstance(member, disnake.Member):
      return list(set(self.premiumroles) & set(member.roles))
    else:
      return False

  def error_embed(self, inter:disnake.Interaction) -> disnake.Embed:
    rolelist = self.bot.babel.string_list(inter, [r.name for r in self.premiumroles], True)
    embed = disnake.Embed(
      title=self.babel(inter, 'required_title'),
      description=self.babel(inter, 'required_error', role=rolelist)
    )
    embed.url = (
      self.config['patreon'] if self.config['patreon']
      else self.config['other']
    )
    embed.set_thumbnail(url=self.config['icon'])
    return embed

  async def check_premium_slash_command(self, inter:disnake.CommandInteraction):
    restricted = self.config['restricted_commands'].split(' ')
    if inter.application_command.name in restricted:
      if await self.check_premium(inter.author):
        return True # user is premium

      await inter.response.send_message(embed=self.error_embed(inter), ephemeral=True)
      return False # user is not premium
    return True # command is not restricted

  @commands.slash_command()
  async def premium(self, inter:disnake.CommandInteraction):
    """
      Learn more about premium.
    """
    embed = disnake.Embed(title=self.babel(inter, 'name'), description=self.babel(inter, 'desc'))

    embed.url = (
      self.config['patreon'] if self.config['patreon']
      else self.config['other']
    )
    embed.set_thumbnail(url=self.config['icon'])

    #BABEL: feature_#,feature_#_desc
    i = 1
    while f'feature_{i}' in self.bot.babel.langs[self.bot.babel.baselang][self.SCOPE]:
      if self.babel(inter, f'feature_{i}') == '':
        i += 1
        continue
      embed.add_field(name=self.babel(inter, f'feature_{i}'),
                      value=self.babel(inter, f'feature_{i}_desc'),
                      inline=False)
      i += 1
    embed.set_footer(text=self.babel(inter, 'fine_print'))

    buttons = None
    if self.bot.config['help']['serverinv']:
      buttons = [
        disnake.ui.Button(emoji='1️⃣', label=self.babel(inter, 'join_server_cta'),
                          url=self.bot.config['help']['serverinv']),
        disnake.ui.Button(emoji='2️⃣', label=self.babel(inter, 'subscribe_cta'), url=embed.url)
      ]

    await inter.response.send_message(embed=embed, components=buttons)


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(Premium(bot))
