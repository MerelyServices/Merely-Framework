"""
  Music - Shares the bot prefix with a partner music bot
"""

from disnake.ext import commands

musicbot_commands = []

class Music(commands.Cog):
  """
  Promotes a musicbot whenever people try to use this bot for music (unless they already have it)
  """
  def __init__(self, bot:commands.Bot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section('music'):
      bot.config.add_section('music')
    if 'music_commands' not in bot.config['music']:
      bot.config['music']['music_commands'] = 'play,pause,stop'
    if 'music_companion' not in bot.config['music']:
      bot.config['music']['music_companion'] = ''
      raise Exception("music/music_companion must be set in order for the music module to work.")
    self.music.update(aliases=bot.config['music']['music_commands'].split(','))

  @commands.command()
  async def music(self, ctx:commands.Context):
    """
    Called whenever a music bot command is called, stays quiet if the bot is already on this server
    """
    if ctx.guild.get_member(int(self.bot.config['music']['music_companion'])) is None:
      await ctx.reply(self.bot.babel(
        ctx,
        'music',
        'promo',
        invite=f"https://discord.com/oauth2/authorize?client_id={self.bot.config['music']['music_companion']}&scope=bot&permissions=0"
      ))
    elif ctx.invoked_with == 'music':
      await ctx.reply(self.bot.babel(ctx, 'music', 'success'))

def setup(bot):
  """ Bind this cog to the bot """
  bot.add_cog(Music(bot))
