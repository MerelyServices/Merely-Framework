import discord
from discord.ext import commands

class Error(commands.cog.Cog):
  """user-friendly error reporting"""
  def __init__(self, bot:commands.Bot):
    self.bot = bot
  
  @commands.Cog.listener("on_command_error")
  async def handle_error(self, ctx:commands.Context, error):
    if isinstance(error, commands.CommandOnCooldown):
      print("cooldown")
      return
    elif isinstance(error, commands.CommandNotFound):
      await ctx.send(f"unable to find a matching command, use `{self.bot.config['main']['prefix_short']}help` to get started.")
    elif isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument):
      if 'Help' in self.bot.cogs:
        await self.bot.cogs['Help'].help(ctx, ctx.command.name)
      else:
        await ctx.send("a required parameter for this command is missing.")
    elif isinstance(error, commands.NoPrivateMessage):
      await ctx.send("this command *can't* be used in private messages.")
    elif isinstance(error, commands.PrivateMessageOnly):
      await ctx.send("this command can **only** be used in private messages.")
    elif isinstance(error, commands.CommandInvokeError):
      await ctx.send("an error occured while trying to run the command, please try again later.")
    raise error

def setup(bot):
  bot.add_cog(Error(bot))