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

  def check_delete(self, message:discord.Message, strict:bool=False):
    return strict or\
      (message.author==self.bot.user or\
      message.content.lower().startswith(self.bot.config['main']['prefix_short']) or\
      message.content.startswith('<@'+str(self.bot.user.id)+'>') or\
      message.type == discord.MessageType.pins_add or\
      (self.bot.config['main']['prefix_long'] and\
      message.content.lower().startswith(self.bot.config['main']['prefix_long']))
      )

  @commands.Cog.listener("on_message")
  async def janitor_autodelete(self, message):
    """janitor service, deletes messages after a time"""
    if f"{message.channel.id}_janitor" in self.bot.config['admin']:
      strict = self.bot.config.getint('admin', f"{message.channel.id}_janitor")
      if self.check_delete(strict):
        await asyncio.sleep(30)
        await message.delete()

  @commands.group()
  @commands.guild_only()
  async def janitor(self, ctx:commands.Context):
    """janitor (join [strict]|leave)
    janitor will auto-delete messages after 30 seconds, resulting in a cleaner channel.
    if you provide the strict flag, janitor will delete all messages, not just messages to and from this bot."""

    if ctx.invoked_subcommand is None:
      raise commands.MissingRequiredArgument
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
  @commands.guild_only()
  async def clean(self, ctx:commands.Context, n_or_id:str=None, strict:str=None):
    """clean (n|start_id-end_id) [strict]
    mass-deletes messages from a channel, n specifies how many messages back to look, 'strict' deletes all messages, not just messages to and from this bot.
    if you instead provide two message ids seperated by a dash, clean will run on this range instead of scanning upwards from the current message."""

    if n_or_id is None:
      raise commands.MissingRequiredArgument
    elif n_or_id.isdigit():
      n = int(n_or_id)
      self.auth.mods(ctx)
      deleted = await ctx.channel.purge(limit=n, check=lambda m:self.check_delete(m, strict))
      await ctx.send(f"deleted {len(deleted)} messages successfully.")
    elif '-' in n_or_id:
      start,end = n_or_id.split('-')
      start,end = int(start),int(end)
      self.auth.mods(ctx)
      if start>end: start,end = end,start
      deleted = await ctx.channel.purge(limit=1000,
                                        check=lambda m: m.id>start and m.id<end and self.check_delete(m, strict),
                                        before=discord.Object(end),
                                        after=discord.Object(start))
      await ctx.send(f"deleted {len(deleted)} messages successfully.")

  @commands.command()
  @commands.cooldown(1, 1)
  async def die(self, ctx:commands.Context, saveconfig=False):
    """die [saveconfig]
    shuts down the bot safely, saves the config file if you provide a value"""
    self.auth.superusers(ctx)
    await ctx.send("shutting down...")
    if saveconfig:
      self.bot.config.save()
    await self.bot.close()


def setup(bot):
  bot.add_cog(Admin(bot))