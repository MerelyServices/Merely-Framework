"""
  Error - Rich error handling cog
  Features: determine the nature of the error and explain what went wrong
  Recommended cogs: Help
"""

from __future__ import annotations

from typing import Union, TYPE_CHECKING
import disnake
from disnake.ext import commands

if TYPE_CHECKING:
  from ..main import MerelyBot


class Error(commands.Cog):
  """user-friendly error reporting"""
  def __init__(self, bot:MerelyBot):
    self.bot = bot

  @commands.Cog.listener('on_user_command_error')
  @commands.Cog.listener('on_message_command_error')
  @commands.Cog.listener('on_slash_command_error')
  @commands.Cog.listener('on_command_error')
  async def handle_error(
    self,
    ctx:Union[commands.Context, disnake.Interaction],
    error:commands.CommandError
  ):
    """ Report to the user what went wrong """
    print("error detected")
    if isinstance(error, commands.CommandOnCooldown):
      if error.cooldown.get_retry_after() > 5:
        await ctx.send(
          self.bot.babel(ctx, 'error', 'cooldown', t=int(error.cooldown.get_retry_after())),
          ephemeral=True
        )
        return
      print("cooldown")
      return
    kwargs = {'ephemeral': True} if isinstance(ctx, disnake.Interaction) else {}
    if isinstance(
      error,
      (commands.CommandNotFound, commands.BadArgument, commands.MissingRequiredArgument)
    ):
      if 'Help' in self.bot.cogs:
        if (
          isinstance(ctx, commands.Context) and isinstance(error, commands.CommandNotFound) and
          ctx.invoked_with in [cmd.name for cmd in self.bot.slash_commands]
        ):
          # Catch when people try to use prefixed commands and nudge them in the right direction
          embed = disnake.Embed(
            title=self.bot.babel(ctx, 'error', 'slash_migration_title'),
            description=self.bot.babel(ctx, 'error', 'slash_migration'),
            color=int(self.bot.config['main']['themecolor'], 16)
          )
          embed.add_field(
            name=self.bot.babel(ctx, 'error', 'slash_migration_problems_title'),
            value=self.bot.babel(
              ctx,
              'error',
              'slash_migration_problems',
              invite=(
                'https://discord.com/oauth2/authorize?client_id=' +
                self.bot.user.id +
                '&scope=bot%20applications.commands&permissions=0'
              )
            )
          )
          try:
            await ctx.send(embed=embed)
          except disnake.Forbidden:
            await ctx.send(
              '\n'.join((
                f'**{embed.title}**',
                embed.description,
                f'*{embed.fields[0].name}*',
                embed.fields[0].value
              ))
            )
        else:
          await self.bot.cogs['Help'].help(
            ctx,
            ctx.invoked_with if isinstance(ctx, commands.Context) else ctx.application_command.name,
            **kwargs
          )
      else:
        await ctx.send(self.bot.babel(ctx, 'error', 'missingrequiredargument'), **kwargs)
      return
    if isinstance(error, commands.NoPrivateMessage):
      await ctx.send(self.bot.babel(ctx, 'error', 'noprivatemessage'), **kwargs)
      return
    if isinstance(error, commands.PrivateMessageOnly):
      await ctx.send(self.bot.babel(ctx, 'error', 'privatemessageonly'), **kwargs)
      return
    if isinstance(error, commands.CommandInvokeError):
      if 'Auth' in self.bot.cogs and isinstance(error.original, self.bot.cogs['Auth'].AuthError):
        await ctx.send(str(error.original), **kwargs)
        return
      await ctx.send(
        self.bot.babel(ctx, 'error', 'commanderror', error=str(error.original)),
        **kwargs
      )
      raise error
    elif isinstance(error, (commands.CheckFailure, commands.CheckAnyFailure)):
      return


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(Error(bot))
