import discord
from discord.ext import commands
from .middleware.auth import Auth,AuthError

class Admin(commands.cog.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.auth = Auth(bot)

  @commands.command()
  @commands.cooldown(1, 1)
  async def die(self, ctx):
    self.auth.superusers(ctx)
    await ctx.send("shutting down...")
    await self.bot.logout()
  @die.error
  async def dieerror(self, ctx, error):
    if isinstance(error.origninal, AuthError):
      await ctx.send(str(error.original))
    else:
      raise error


def setup(bot):
  bot.add_cog(Admin(bot))