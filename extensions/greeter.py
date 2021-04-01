import discord
from discord.ext import commands
from .auth import Auth

class Greeter(commands.cog.Cog):
  def __init__(self, bot : commands.Bot):
    self.bot = bot
    if not bot.config.getboolean('extensions', 'auth', fallback=False):
      raise Exception("'auth' must be enabled to use 'greeter'")
    if not bot.config.getboolean('extensions', 'help', fallback=False):
      print(Warning("'help' is a recommended extension for 'greeter'"))
    self.auth = Auth(bot)
    # ensure config file has required data
    if not bot.config.has_section('greeter'):
      bot.config.add_section('greeter')

  @commands.Cog.listener()
  async def on_member_join(self, member):
    """welcome service, shows a custom welcome message to new users"""
    if f"{member.guild.id}_welcome" in self.bot.config['greeter']:
      data = self.bot.config['greeter'][f"{member.guild.id}_welcome"].split(', ')
      channel = member.guild.get_channel(int(data[0]))
      await channel.send(', '.join(data[1:]).format(member.mention, member.guild.name))

  @commands.Cog.listener()
  async def on_member_leave(self, member):
    """farewell service, shows a custom farewell message whenever someone leaves"""
    if f"{member.guild.id}_farewell" in self.bot.config['greeter']:
      data = self.bot.config['greeter'][f"{member.guild.id}_farewell"].split(', ')
      channel = member.guild.get_channel(int(data[0]))
      await channel.send(', '.join(data[1:]).format(f"{member.name}#{member.discriminator}", member.guild.name))
  
  # TODO: add error handling module with support for commands.errors.NoPrivateMessage
  @commands.group()
  @commands.guild_only()
  async def welcome(self, ctx):
    """welcome (get|set|clear)
    control the welcome message for your server
    use `set` to get instructions on how to set a new welcome message"""
    if ctx.invoked_subcommand is None and 'Help' in self.bot.cogs:
      await self.bot.cogs['Help'].help(ctx, 'welcome')
  @welcome.command(name='get')
  async def welcome_get(self, ctx):
    if f'{ctx.guild.id}_welcome' in self.bot.config['greeter']:
      data = self.bot.config['greeter'][f"{ctx.guild.id}_welcome"].split(', ')
      await ctx.send("in "+ctx.guild.get_channel(int(data[0])).mention+": "+', '.join(data[1:]).format('@USER', ctx.guild.name))
    else:
      await self.welcome_set(ctx)
  @welcome.command(name='set')
  async def welcome_set(self, ctx, *, message=None):
    self.auth.admins(ctx)
    if not message:
      await ctx.send("to set a welcome message, use\n"+\
                     f"`{self.bot.config['main']['prefix_short']}welcome set Welcome, {{}} to the {{}} server!` (as an example)\n"+\
                     "*the first {} will become a mention of the new user, and the second {} will be the current server name.*")
    else:
      self.bot.config['greeter'][f'{ctx.guild.id}_welcome'] = f"{ctx.channel.id}, {message}"
      self.bot.config.save()
      await ctx.send("successfully set the welcome message!")
  @welcome.command(name='clear')
  async def welcome_clear(self, ctx):
    self.auth.admins(ctx)
    if f'{ctx.guild.id}_welcome' in self.bot.config['greeter']:
      self.bot.config.remove_option('greeter', f'{ctx.guild.id}_welcome')
      self.bot.config.save()
      await ctx.send("removed and disabled the welcome message.")
    else:
      await ctx.send("you don't currently have a welcome message set!")
    
  @commands.group(no_pm=True)
  @commands.guild_only()
  async def farewell(self, ctx):
    """farewell (get|set|clear)
    control the farewell message for your server
    use `set` to get instructions on how to set a new farewell message"""
    if ctx.invoked_subcommand is None and 'Help' in self.bot.cogs:
      await self.bot.cogs['Help'].help(ctx, 'farewell')
  @farewell.command(name='get')
  async def farewell_get(self, ctx):
    if f'{ctx.guild.id}_farewell' in self.bot.config['greeter']:
      data = self.bot.config['greeter'][f"{ctx.guild.id}_farewell"].split(', ')
      await ctx.send("in "+ctx.guild.get_channel(int(data[0])).mention+": "+', '.join(data[1:]).format('USER#1234', ctx.guild.name))
    else:
      await self.farewell_set(ctx)
  @farewell.command(name='set')
  async def farewell_set(self, ctx, *, message=None):
    self.auth.admins(ctx)
    if not message:
      await ctx.send("to set a farewell message, use\n"+\
                     f"`{self.bot.config['main']['prefix_short']}farewell set {{}} has left the {{}} server` (as an example)\n"+\
                     "*the first {} will become the username of the leaving user, and the second {} will be the current server name.*")
    else:
      self.bot.config['greeter'][f'{ctx.guild.id}_farewell'] = f"{ctx.channel.id}, {message}"
      self.bot.config.save()
      await ctx.send("successfully set the farewell message!")
  @farewell.command(name='clear')
  async def farewell_clear(self, ctx):
    self.auth.admins(ctx)
    if f'{ctx.guild.id}_farewell' in self.bot.config['greeter']:
      self.bot.config.remove_option('greeter', f'{ctx.guild.id}_farewell')
      self.bot.config.save()
      await ctx.send("removed and disabled the farewell message.")
    else:
      await ctx.send("you don't currently have a farewell message set!")
  

def setup(bot):
  bot.add_cog(Greeter(bot))