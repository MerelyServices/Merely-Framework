"""
  Auth - One-liner authorization checks for commands
  Throws AuthError to quickly exit the command
  From there, Error can tell the users why the command failed
  Recommended cogs: Error
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import disnake

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


class Auth():
  """ Backup permissions/auth verification when guild permissions aren't in effect """
  SCOPE = 'auth'

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
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

  def superusers(self, inter:disnake.Interaction, fail=True) -> bool:
    """ Verify this user is a superuser """
    if str(inter.author.id) in self.config['superusers']:
      return True
    if fail:
      raise self.AuthError(self.babel(inter, 'not_superuser'))
    return False

  def owners(self, inter:disnake.Interaction, fail=True) -> bool:
    """ Verify this user owns this guild """
    if self.superusers(inter, fail=False):
      return True
    if isinstance(inter, disnake.GuildCommandInteraction) and inter.author == inter.guild.owner:
      return True
    if fail:
      raise self.AuthError(self.babel(inter, 'unauthorized'))
    return False

  def admins(self, inter:disnake.Interaction, fail=True) -> bool:
    """ Verify this user is an admin """
    if self.owners(inter, fail=False):
      return True
    if inter.permissions.administrator:
      return True
    if fail:
      raise self.AuthError(self.babel(inter, 'not_admin'))
    return False

  def authusers(self, inter:disnake.Interaction, fail=True) -> bool:
    """ Verify this user is an authuser """
    if self.superusers(inter, fail=False):
      return True
    if str(inter.author.id) in self.config['authusers']:
      return True
    if fail:
      raise self.AuthError(self.babel(inter, 'not_authuser'))
    return False

  def mods(self, inter:disnake.Interaction, fail=True) -> bool:
    """ Verify this user is a moderator """
    if self.authusers(inter, fail=False):
      return True
    if self.admins(inter, fail=False):
      return True
    if inter.permissions.ban_members:
      return True
    if fail:
      raise self.AuthError(self.babel(inter, 'not_mod'))
    return False
