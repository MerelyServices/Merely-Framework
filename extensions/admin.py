import discord, asyncio
from discord.ext import commands
from .auth import Auth

class Admin(commands.cog.Cog):
  def __init__(self, bot : commands.Bot):
    self.bot = bot
    if not bot.config.getboolean('extensions', 'auth', fallback=False):
      raise Exception("'auth' must be enabled to use 'admin'")
    self.auth = Auth(bot)
    # ensure config file has required data
    if not bot.config.has_section('admin'):
      bot.config.add_section('admin')
    if 'logchannel' not in bot.config['admin']:
      bot.config['admin']['logchannel'] = ''
    if 'owneroptout' not in bot.config['admin']:
      bot.config['admin']['owneroptout'] = ''

  @commands.Cog.listener()
  async def on_message(self, message):
    """janitor service, deletes messages after a time"""
    if f"{message.channel.id}_janitor" in self.bot.config['admin']:
      # 0 is relaxed, 1 is strict.
      lvl = self.bot.config.getint('admin', f"{message.channel.id}_janitor")
      if lvl == 1 or\
         (lvl == 0 and message.author==self.bot.user or self.bot.user in message.mentions or\
          message.content.lower().startswith(self.bot.config['main']['prefix_short']) or\
           (self.bot.config['main']['prefix_long'] and\
           message.content.lower().startswith(self.bot.config['main']['prefix_long'])
          )
         ):
        await asyncio.sleep(30)
        await message.delete()

  @commands.command()
  @commands.cooldown(1, 1)
  async def die(self, ctx, saveconfig=False):
    """die [saveconfig]
    shuts down the bot cleanly, saves the config file if you provide a value"""
    self.auth.superusers(ctx)
    await ctx.send("shutting down...")
    if saveconfig:
      self.bot.config.save()
    await self.bot.logout()
  @die.error
  async def dieerror(self, ctx, error):
    if isinstance(error, commands.errors.CommandOnCooldown):
      return
    raise error


def setup(bot):
  bot.add_cog(Admin(bot))