class AuthError(Exception):
  """Errors to be sent to a user that failed an auth test"""
  pass

class Auth:
  def __init__(self, bot):
    self.bot = bot
  
  def owners(self, ctx):
      if ctx.message.author == ctx.message.guild.owner or\
         str(str(ctx.message.author.id)) in self.bot.config['auth']['superusers']:
        return True
      else:
        raise AuthError("you must be a server owner to use this command!")

  def admins(self, ctx):
      if ctx.message.author == ctx.message.guild.owner or\
         ctx.message.author.permissions_in(ctx.channel).administrator or\
         str(ctx.message.author.id) in self.bot.config['auth']['superusers']:
        return True
      else:
        raise AuthError("you must be an admin to use this command!")

  def mods(self, ctx):
      if ctx.message.author == ctx.message.guild.owner or\
         ctx.message.author.permissions_in(ctx.channel).administrator or\
         ctx.message.author.permissions_in(ctx.channel).ban_members or\
         str(ctx.message.author.id) in self.bot.config['auth']['superusers'] or\
         str(ctx.message.author.id) in self.bot.config['auth']['authusers']:
        return True
      else:
        raise AuthError("you must be a moderator to use this command!")

  def superusers(self, ctx):
      if str(ctx.message.author.id) in self.bot.config['auth']['superusers']:
        return True
      else:
        raise AuthError("you must be a superuser of this bot to use this command!")

  def superusers(self, ctx):
      if str(ctx.message.author.id) in self.bot.config['auth']['superusers'] or\
         str(ctx.message.author.id) in self.bot.config['auth']['authusers']:
        return True
      else:
        raise AuthError("you must be an authuser of this bot to use this command!")