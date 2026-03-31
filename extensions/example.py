"""
  Example - Simple extension for Merely Framework
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

from extensions.controlpanel import ControlPanelCog, Toggleable, Listable, Selectable, Stringable

if TYPE_CHECKING:
  from main import MerelyBot


class Example(ControlPanelCog):
  """ Example commands for learning purposes """
  SCOPE = 'example'

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)

    # Add context menu commands
    self.example_user = app_commands.ContextMenu(
      name='Example',
      allowed_contexts=app_commands.AppCommandContext(guild=True, private_channel=True),
      allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
      callback=self.example_user_callback
    )
    bot.tree.add_command(self.example_user)

    self.example_msg = app_commands.ContextMenu(
      name='Example',
      allowed_contexts=app_commands.AppCommandContext(guild=True, private_channel=True),
      allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
      callback=self.example_msg_callback
    )
    bot.tree.add_command(self.example_msg)

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

  async def example_user_callback(self, inter:discord.Interaction, user:discord.User):
    """ Responds with user information """
    await inter.response.send_message(
      '```' + '\n'.join([user.name, str(user.id)]) + '```', ephemeral=True
    )

  async def example_msg_callback(self, inter:discord.Interaction, msg:discord.Message):
    """ Responds with message information """
    await inter.response.send_message(
      '```' + '\n'.join([msg.author.name, str(msg.id)]) + '```', ephemeral=True
    )

  @app_commands.command()
  @app_commands.allowed_contexts(guilds=True, private_channels=True)
  @app_commands.allowed_installs(guilds=True, users=True)
  async def example(self, inter:discord.Interaction, echo:str):
    """ Just a simple echo command """
    await inter.response.send_message(echo, ephemeral=True)


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Example(bot))
