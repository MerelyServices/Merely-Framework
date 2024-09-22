"""
  Example - Simple extension for Merely Framework
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

from extensions.controlpanel import Toggleable, Listable, Selectable, Stringable

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


class Example(commands.Cog):
  """ Adds an echo command and logs new members """
  SCOPE = 'example'

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
    #if not bot.config.has_section(self.SCOPE):
      #bot.config.add_section(self.SCOPE)

  def controlpanel_settings(self, inter:discord.Interaction):
    # ControlPanel integration - use this when you want to allow users / guilds to change preferences
    return [
      Toggleable(self.SCOPE, 'toggle', 'toggle', False),
      Listable(self.SCOPE, 'list', 'list', str(inter.user.id)),
      Selectable(self.SCOPE, 'select', 'select', [
        discord.SelectOption(label=val) for val in ['a', 'b', 'c']
      ]),
      Stringable(self.SCOPE, 'string', 'string')
    ]

  def controlpanel_theme(self) -> tuple[str, discord.ButtonStyle]:
    # Controlpanel custom theme for buttons
    return (self.SCOPE, discord.ButtonStyle.gray)

  @commands.Cog.listener()
  async def on_member_join(self, member:discord.Member):
    """ Record to log when a member joins """
    # Using the guild as the language target. Usually you just use inter instead.
    print(self.babel(member.guild, 'joined', user=member.name))
    # babel will return "{JOINED: user=member.name}" until a string is added to en.ini

  @app_commands.command()
  @app_commands.allowed_contexts(guilds=True, private_channels=True)
  @app_commands.allowed_installs(guilds=True, users=True)
  async def example(self, inter:discord.Interaction, echo:str):
    """ Just a simple echo command """
    await inter.response.send_message(echo, ephemeral=True)


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Example(bot))
