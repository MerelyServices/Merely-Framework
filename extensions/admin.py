import discord, asyncio
from discord.ext import commands

class Admin(commands.cog.Cog):
  def __init__(self, bot:commands.Bot):
    self.bot = bot
    if not bot.config.getboolean('extensions', 'auth', fallback=False):
      raise Exception("'auth' must be enabled to use 'admin'")
    self.auth = bot.cogs['Auth']
    # ensure config file has required data
    if not bot.config.has_section('admin'):
      bot.config.add_section('admin')
    if 'logchannel' not in bot.config['admin']:
      bot.config['admin']['logchannel'] = ''
    if 'owneroptout' not in bot.config['admin']:
      bot.config['admin']['owneroptout'] = ''

  @commands.Cog.listener("on_message")
  async def janitor_autodelete(self, message):
    """janitor service, deletes messages after a time"""
    if f"{message.channel.id}_janitor" in self.bot.config['admin']:
      # 0 is relaxed, 1 is strict.
      lvl = self.bot.config.getint('admin', f"{message.channel.id}_janitor")
      if lvl == 1 or\
         (lvl == 0 and message.author==self.bot.user or self.bot.user in message.mentions or\
          message.content.lower().startswith(self.bot.config['main']['prefix_short']) or\
          (self.bot.config['main']['prefix_long'] and\
          message.content.lower().startswith(self.bot.config['main']['prefix_long']))
         ):
        await asyncio.sleep(30)
        await message.delete()

  @commands.group()
  @commands.guild_only()
  async def janitor(self, ctx:commands.Context):
    """janitor (join [strict]|leave)
    janitor will auto-delete messages after 30 seconds, resulting in a cleaner channel.
    if you provide the strict flag, janitor will delete all messages, not just messages to and from this bot.
    """
    if ctx.invoked_subcommand is None:
      if 'Help' in self.bot.cogs:
        await self.bot.cogs['Help'].help(ctx, 'janitor')
    else:
      self.auth.admins(ctx)
  @janitor.command(name='join')
  async def janitor_join(self, ctx:commands.Context, strict=''):
    self.bot.config['admin'][f'{ctx.channel.id}_janitor'] = '1' if strict else '0'
    self.bot.config.save()
    await ctx.send("successfully added or updated the janitor for this channel.")
  @janitor.command(name='leave')
  async def janitor_leave(self, ctx:commands.Context):
    self.bot.config.remove_option('admin', f'{ctx.channel.id}_janitor')
    self.bot.config.save()
    await ctx.send("successfully removed the janitor for this channel.")

  @commands.command()
  @commands.cooldown(1, 1)
  async def die(self, ctx:commands.Context, saveconfig=False):
    """die [saveconfig]
    shuts down the bot cleanly, saves the config file if you provide a value"""
    self.auth.superusers(ctx)
    await ctx.send("shutting down...")
    if saveconfig:
      self.bot.config.save()
    await self.bot.close()


def setup(bot):
  bot.add_cog(Admin(bot))