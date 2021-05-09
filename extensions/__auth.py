import discord
from discord.ext import commands

class Auth(commands.Cog):
  """custom auth rules for merely framework"""
  def __init__(self, bot:commands.Bot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section('auth'):
      bot.config.add_section('auth')
    if 'superusers' not in bot.config['auth']:
      bot.config['auth']['superusers'] = ''
    if 'authusers' not in bot.config['auth']:
      bot.config['auth']['authusers'] = ''
  
  @commands.Cog.listener("on_command_error")
  async def check_autherror(self, ctx:commands.Context, error):
    if isinstance(error, commands.errors.CommandInvokeError):
      if error.original is AuthError:
        await ctx.send(str(error.original))

  def owners(self, ctx:commands.Context):
      if ctx.message.author == ctx.message.guild.owner or\
         str(str(ctx.message.author.id)) in self.bot.config['auth']['superusers']:
        return True
      else:
        raise AuthError("you must be a server owner to use this command!")

  def admins(self, ctx:commands.Context):
      if ctx.message.author == ctx.message.guild.owner or\
         ctx.message.author.permissions_in(ctx.channel).administrator or\
         str(ctx.message.author.id) in self.bot.config['auth']['superusers']:
        return True
      else:
        raise AuthError("you must be an admin to use this command!")

  def mods(self, ctx:commands.Context):
      if ctx.message.author == ctx.message.guild.owner or\
         ctx.message.author.permissions_in(ctx.channel).administrator or\
         ctx.message.author.permissions_in(ctx.channel).ban_members or\
         str(ctx.message.author.id) in self.bot.config['auth']['superusers'] or\
         str(ctx.message.author.id) in self.bot.config['auth']['authusers']:
        return True
      else:
        raise AuthError("you must be a moderator to use this command!")

  def superusers(self, ctx:commands.Context):
      if str(ctx.message.author.id) in self.bot.config['auth']['superusers']:
        return True
      else:
        raise AuthError("you must be a superuser of this bot to use this command!")

  def authusers(self, ctx:commands.Context):
      if str(ctx.message.author.id) in self.bot.config['auth']['superusers'] or\
         str(ctx.message.author.id) in self.bot.config['auth']['authusers']:
        return True
      else:
        raise AuthError("you must be an authuser of this bot to use this command!")

class AuthError(Exception):
  """Errors to be sent to a user that failed an auth test"""
  pass

def setup(bot):
  bot.add_cog(Auth(bot))