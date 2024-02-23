"""
  Prefix - change the activation prefix in text mode
  Mostly useless now as Discord heavily encourages using slash commands instead
  Keeping only for custom bots on small servers
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import disnake
from disnake.ext import commands

from .controlpanel import Toggleable, Selectable, Stringable

if TYPE_CHECKING:
  from ..main import MerelyBot
  from ..babel import Resolvable


class Prefix(commands.Cog):
  """ Change the prefix used to activate this bot """
  SCOPE = 'prefix'

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
    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)
    self.fallback_prefix = bot.command_prefix
    bot.command_prefix = self.check_prefix

  def controlpanel_settings(self) -> list[Toggleable | Selectable | Stringable]:
    # ControlPanel integration
    return [
      Stringable("Prefix", self.bot.config, self.SCOPE, '{g}')
    ]

  def check_prefix(self, bot, message:disnake.Message):
    if isinstance(message.channel, disnake.TextChannel):
      if (
        str(message.channel.guild.id) in self.config and
        len(self.config[str(message.channel.guild.id)])
      ):
        if message.content.lower().startswith(self.config[str(message.channel.guild.id)].lower()):
          return [message.content[0:len(self.config[str(message.channel.guild.id)])]]
        return commands.when_mentioned(bot, message)
    return self.fallback_prefix(bot, message)

  @commands.group()
  @commands.guild_only()
  async def prefix(self, ctx:commands.Context):
    if ctx.invoked_subcommand is None:
      raise commands.errors.BadArgument
    else:
      self.bot.cogs['Auth'].admins(ctx.message)

  @prefix.command(name='set')
  async def prefix_set(self, ctx:commands.Context, prefix:str, guild:int = 0):
    prefix = prefix.strip(' ')
    if guild:
      self.bot.cogs['Auth'].authusers(ctx.message)
    self.config[str(guild if guild else ctx.guild.id)] = prefix
    self.bot.config.save()
    await ctx.reply(self.babel(ctx, 'set_success', prefix=prefix))

  @prefix.command(name='unset')
  async def prefix_unset(self, ctx:commands.Context, guild:int = 0):
    if guild:
      self.bot.cogs['Auth'].authusers(ctx.message)
    self.bot.config.remove_option(self.SCOPE, str(guild if guild else ctx.guild.id))
    self.bot.config.save()
    await ctx.reply(self.babel(ctx, 'unset_success'))

  @prefix.command(name='get')
  async def prefix_get(self, ctx:commands.Context, guild:int = 0):
    await ctx.reply(self.babel(ctx, 'get', prefix=self.bot.config.get(
      self.SCOPE,
      str(guild if guild else ctx.guild.id),
      fallback='*unset*')
    ))


def setup(bot:MerelyBot):
  bot.add_cog(Prefix(bot))
