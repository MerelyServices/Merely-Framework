"""
  Premium - exclusive functionality for paying users
  Still rather primitive, prevents usage of an entire command unless a user has a certain role
  Currently unused until new premium exclusive features are developed
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import disnake
from disnake.ext import commands

if TYPE_CHECKING:
  from ..main import MerelyBot


class Premium(commands.Cog):
  premiumguild: disnake.Guild
  premiumroles: list[disnake.Role]

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section('premium'):
      bot.config.add_section('premium')
    if 'icon' not in bot.config['premium']:
      bot.config['premium']['icon'] = ''
    if 'patreon' not in bot.config['premium']:
      bot.config['premium']['patreon'] = ''
    if 'other' not in bot.config['premium']:
      bot.config['premium']['other'] = ''
    if 'restricted_commands' not in bot.config['premium']:
      bot.config['premium']['restricted_commands'] = ''
    if 'premium_role_guild' not in bot.config['premium'] or\
       not bot.config['premium']['premium_role_guild'] or\
       'premium_roles' not in bot.config['premium'] or\
       not bot.config['premium']['premium_roles']:
      bot.config['premium']['premium_role_guild'] = ''
      bot.config['premium']['premium_roles'] = ''
      raise Exception(
        "You must provide a reference to a guild and at least one role in order for premium to work!"
      )
    if not bot.config.get('help', 'serverinv', fallback=''):
      raise Exception(
        "You must have an invite to the support server with the supporter role in " +
        "config[help][serverinv]!"
      )

    self.premiumguild = None
    self.premiumroles = []

    bot.add_check(self.check_premium_command)
    bot.add_app_command_check(self.check_premium_slash_command, slash_commands=True)

  @commands.Cog.listener('on_connect')
  async def cache_role(self):
    """ Fetches guild and member list on connect to decrease first response time """
    self.premiumguild = self.bot.get_guild(self.bot.config.getint('premium', 'premium_role_guild'))
    self.premiumroles = [
      self.premiumguild.get_role(int(i)) for i in self.bot.config.get('premium', 'premium_roles')
      .split(' ')
    ]
    if not self.premiumroles:
      raise Exception("The designated premium role was not found!")

  async def check_premium(self, user:disnake.User):
    member = await self.premiumguild.fetch_member(user.id)
    if isinstance(member, disnake.Member):
      return list(set(self.premiumroles) & set(member.roles))
    else:
      return False

  async def check_premium_command(self, ctx:commands.Context):
    if ctx.command.name in self.bot.config['premium']['restricted_commands'].split(' '):
      if await self.check_premium(ctx.author):
        return True # user is premium
      rolelist = self.bot.babel.string_list(ctx, [r.name for r in self.premiumroles])
      embed = disnake.Embed(
        title=self.bot.babel(ctx, 'premium', 'required_title'),
        description=self.bot.babel(ctx, 'premium', 'required_error', role=rolelist)
      )
      embed.url = (
        self.bot.config['premium']['patreon'] if self.bot.config['premium']['patreon']
        else self.bot.config['premium']['other']
      )
      embed.set_thumbnail(url=self.bot.config['premium']['icon'])

      await ctx.reply(embed=embed)
      return False # user is not premium
    return True # command is not restricted

  async def check_premium_slash_command(self, inter:disnake.CommandInteraction):
    restricted = self.bot.config['premium']['restricted_commands'].split(' ')
    if inter.application_command.name in restricted:
      if await self.check_premium(inter.author):
        return True # user is premium
      rolelist = self.bot.babel.string_list(inter, [r.name for r in self.premiumroles])
      embed = disnake.Embed(
        title=self.bot.babel(inter, 'premium', 'required_title'),
        description=self.bot.babel(inter, 'premium', 'required_error', role=rolelist)
      )
      embed.url = (
        self.bot.config['premium']['patreon'] if self.bot.config['premium']['patreon']
        else self.bot.config['premium']['other']
      )
      embed.set_thumbnail(url=self.bot.config['premium']['icon'])

      await inter.response.send_message(embed=embed, ephemeral=True)
      return False # user is not premium
    return True # command is not restricted

  @commands.slash_command()
  async def premium(self, inter:disnake.CommandInteraction):
    """
      Learn more about premium.
    """
    embed = disnake.Embed(title=self.bot.babel(inter, 'premium', 'name'),
                          description=self.bot.babel(inter, 'premium', 'desc'))

    embed.url = (
      self.bot.config['premium']['patreon'] if self.bot.config['premium']['patreon']
      else self.bot.config['premium']['other']
    )
    embed.set_thumbnail(url=self.bot.config['premium']['icon'])

    i = 1
    while f'feature_{i}' in self.bot.babel.langs[self.bot.babel.baselang]['premium']:
      if self.bot.babel(inter, 'premium', f'feature_{i}') == '':
        continue
      embed.add_field(name=self.bot.babel(inter, 'premium', f'feature_{i}'),
                      value=self.bot.babel(inter, 'premium', f'feature_{i}_desc'),
                      inline=False)
      i += 1

    embed.set_footer(text=self.bot.babel(inter, 'premium', 'fine_print'))

    await inter.response.send_message(
      self.bot.babel(inter, 'premium', 'cta', link=embed.url), embed=embed
    )


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(Premium(bot))
