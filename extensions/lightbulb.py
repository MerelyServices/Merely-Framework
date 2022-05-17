import disnake
from disnake.ext import commands
from typing import Dict, Pattern, Optional
import re, asyncio

class LightbulbDriver():
  """just a simple data class"""
  name:str
  pattern:Pattern
  action:Optional[str]

  def __init__(self, bot:commands.Bot):
    self.bot = bot
  
  def set_pattern(self, pattern:str):
    self.pattern = re.compile(pattern)
  
  def set_action(self, action:str):
    actcmd = action.split()[0]
    if [cmd for cmd in self.bot.commands if cmd.name == actcmd or actcmd in cmd.aliases]:
      self.action = action
    else:
      self.action = None

class Lightbulb(commands.Cog):
  """a prototype service for commandless bots"""
  drivers:Dict[str, LightbulbDriver] = {}

  def __init__(self, bot:commands.Bot):
    self.bot = bot
    if not bot.config.getboolean('extensions', 'auth', fallback=False):
      raise Exception("'auth' must be enabled to use 'admin'")
    self.auth = bot.cogs['Auth']
    # ensure config file has required data
    if not bot.config.has_section('lightbulb'):
      bot.config.add_section('lightbulb')
    if 'opt_in' not in bot.config['lightbulb']:
      bot.config['lightbulb']['opt_in'] = ''


  @commands.Cog.listener("on_ready")
  async def populate_drivers(self):
    for k,v in self.bot.config['lightbulb'].items():
      if k.endswith('_pattern') or k.endswith('_action'):
        name = k[:k.rfind('_')]
        if name not in self.drivers:
          self.drivers[name] = LightbulbDriver(self.bot)
          self.drivers[name].name = name
        if k.endswith('_pattern'):
          self.drivers[name].set_pattern(v)
        else:
          self.drivers[name].set_action(v)
    for k in list(self.drivers.keys()):
      if not self.drivers[k].action:
        faileddriver = self.drivers.pop(k)
        print(f"WARN: unable to find command ({v}) for: {faileddriver.name}")
  
  def scan_message(self, message:disnake.Message):
    if not message.author.bot:
      for driver in self.drivers.values():
        match = driver.pattern.search(message.content)
        if match:
          return match, driver
    return None, None

  @commands.Cog.listener('on_message')
  async def check_message(self, message:disnake.Message):
    if isinstance(message.channel, disnake.channel.TextChannel) and\
       str(message.guild.id) in self.bot.config.get('lightbulb', 'opt_in', fallback='').split():
      match, driver = self.scan_message(message)
      if match:
        await message.add_reaction('💡')
        try:
          await asyncio.sleep(300)
          await message.remove_reaction('💡', self.bot.user)
        except:
          pass

  @commands.Cog.listener('on_reaction_add')
  async def check_reactions(self, reaction:disnake.Reaction, user:disnake.User):
    if not user.bot and str(reaction.emoji) == '💡' and\
       isinstance(reaction.message.channel, disnake.channel.TextChannel) and\
       str(reaction.message.guild.id) in self.bot.config.get('lightbulb', 'opt_in', fallback='').split():
      match, driver = self.scan_message(reaction.message)
      if match:
        message = reaction.message
        message.content = self.bot.config['main']['prefix_short']+driver.action+' '+' '.join(match.groups())
        await self.bot.process_commands(message)
  
  @commands.group()
  @commands.guild_only()
  async def lightbulb(self, ctx:commands.Context):
    if ctx.invoked_subcommand is None:
      raise commands.errors.BadArgument
    else:
      self.auth.admins(ctx)
  @lightbulb.command(name='enable')
  async def lightbulb_enable(self, ctx:commands.Context):
    if str(ctx.guild.id) not in self.bot.config.get('lightbulb', 'opt_in', fallback='').split():
      self.bot.config['lightbulb']['opt_in'] += str(ctx.guild.id) + ' '
      self.bot.config.save()
      await ctx.reply(self.bot.babel(ctx, 'lightbulb', 'enable_success'))
    else:
      await ctx.reply(self.bot.babel(ctx, 'lightbulb', 'already_enabled'))
  @lightbulb.command(name='disable')
  async def lightbulb_disable(self, ctx:commands.Context):
    if str(ctx.guild.id) in self.bot.config.get('lightbulb', 'opt_in', fallback='').split():
      self.bot.config['lightbulb']['opt_in'] = self.bot.config.get('lightbulb', 'opt_in').replace(str(ctx.guild.id) + ' ', '')
      self.bot.config.save()
      await ctx.reply(self.bot.babel(ctx, 'lightbulb', 'disable_success'))
    else:
      await ctx.reply(self.bot.babel(ctx, 'lightbulb', 'already_disabled'))

def setup(bot:commands.Bot):
  bot.add_cog(Lightbulb(bot))