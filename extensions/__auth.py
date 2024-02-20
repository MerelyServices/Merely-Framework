"""
  Auth - One-liner authorization checks for commands
  Throws AuthError to quickly exit the command
  From there, Error can tell the users why the command failed
  Recommended cogs: Error
"""

from __future__ import annotations

from typing import Union, TYPE_CHECKING
import disnake
from disnake.ext import commands

if TYPE_CHECKING:
  from ..main import MerelyBot
  from ..babel import Resolvable


class Auth(commands.Cog):
  """ Backup permissions/auth verification when guild permissions aren't in effect """
  SCOPE = 'auth'

  @property
  def config(self) -> dict[str, str]:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)
    if 'botadmin_guilds' not in self.config:
      self.config['botadmin_guilds'] = ''
    if 'superusers' not in self.config:
      self.config['superusers'] = ''
    if 'authusers' not in self.config:
      self.config['authusers'] = ''

  class AuthError(Exception):
    """Errors to be sent to a user that failed an auth test"""

  def owners(self, msg:Union[disnake.Message, disnake.GuildCommandInteraction]):
    """ Verify this user owns this guild """
    if msg.author == msg.guild.owner or\
       str(str(msg.author.id)) in self.config['superusers']:
      return True
    raise self.AuthError(self.babel(msg, 'unauthorized'))

  def admins(self, msg:Union[disnake.Message, disnake.GuildCommandInteraction]):
    """ Verify this user is an admin """
    if msg.author == msg.guild.owner or\
       msg.channel.permissions_for(msg.author).administrator or\
       str(msg.author.id) in self.config['superusers']:
      return True
    raise self.AuthError(self.babel(msg, 'not_admin'))

  def mods(self, msg:Union[disnake.Message, disnake.GuildCommandInteraction]):
    """ Verify this user is a moderator """
    if msg.author == msg.guild.owner or\
       msg.channel.permissions_for(msg.author).administrator or\
       msg.channel.permissions_for(msg.author).ban_members or\
       str(msg.author.id) in self.config['superusers'] or\
       str(msg.author.id) in self.config['authusers']:
      return True
    raise self.AuthError(self.babel(msg, 'not_mod'))

  def superusers(self, msg:Union[disnake.Message, disnake.CommandInteraction]):
    """ Verify this user is a superuser """
    if str(msg.author.id) in self.config['superusers']:
      return True
    raise self.AuthError(self.babel(msg, 'not_superuser'))

  def authusers(self, msg:Union[disnake.Message, disnake.CommandInteraction]):
    """ Verify this user is an authuser """
    if str(msg.author.id) in self.config['superusers'] or\
       str(msg.author.id) in self.config['authusers']:
      return True
    raise self.AuthError(self.babel(msg, 'not_authuser'))


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(Auth(bot))
