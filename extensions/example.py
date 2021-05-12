import discord
from discord.ext import commands

class Example(commands.cog.Cog):
  def __init__(self, bot:commands.Bot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section('example'):
      bot.config.add_section('example')
  
  @commands.Cog.listener()
  async def on_member_join(self, member):
    print(f"{member.name} has joined!")
  
  @commands.command()
  async def example(self, ctx:commands.Context, *, echo:str):
    """example (echo)
    repeats whatever you say back to you"""
    await ctx.send(echo)

def setup(bot):
  bot.add_cog(Example(bot))