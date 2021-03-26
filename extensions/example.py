import discord
from discord.ext import commands

class Example(commands.cog.Cog):
  def __init__(self, bot):
    self.bot = bot

def setup(bot):
  bot.add_cog(Example(bot))