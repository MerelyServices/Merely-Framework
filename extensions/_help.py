import discord
from discord.ext import commands
import re

class Help(commands.cog.Cog):
  def __init__(self, bot:commands.Bot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section('help'):
      bot.config.add_section('help')
    if 'helpurl' not in bot.config['help']:
      bot.config['help']['helpurl'] = ''
    if 'helpurlvideoexamples' not in bot.config['help']:
      bot.config['help']['helpurlvideoexamples'] = ''
    if 'serverinv' not in bot.config['help']:
      bot.config['help']['serverinv'] = ''
    if 'feedbackchannel' not in bot.config['help']:
      bot.config['help']['feedbackchannel'] = ''
    if 'highlight_sections' not in bot.config['help']:
      bot.config['help']['highlight_sections'] = '💡 learn'
    if 'learn_highlights' not in bot.config['help']:
      bot.config['help']['learn_highlights'] = 'help'
    if 'future_commands' not in bot.config['help']:
      bot.config['help']['future_commands'] = ''
    if 'obsolete_commands' not in bot.config['help']:
      bot.config['help']['obsolete_commands'] = ''
    if 'changelog' not in bot.config['help']:
      bot.config['help']['changes'] = '> '+bot.config['main']['ver']+'\n- No changes yet!'
  
  @commands.command(aliases=['?','??'])
  async def help(self, ctx:commands.Context, command=None):
    """finds usage information in babel and sends them
    highlights some commands if command is None"""
    
    ecommands = {c.name for c in self.bot.commands}

    if command:
      # return usage information for a specific command
      if command in ecommands:
        currentlang = self.bot.babel.langs[self.bot.babel.resolve_lang(ctx)[0]]
        for key in currentlang.keys():
          if f'command_{command}_help' in currentlang[key]:
            docsrc = currentlang[key][f'command_{command}_help']
            docs = '**'+docsrc[0]+'**'
            if len(docsrc) > 1:
              docs += '\n'+docsrc[1]
            if len(docsrc) > 2:
              for line in docsrc[2:]:
                docs += '\n*'+line+'*'
            await ctx.send(docs)
            break
        else:
          await ctx.send(self.bot.babel(ctx, 'help', 'no_docs'))
      else:
        if command in self.bot.config['help']['future_commands'].split(', '):
          await ctx.send(self.bot.babel(ctx, 'help', 'future_command'))
        elif command in self.bot.config['help']['obsolete_commands'].split(', '):
          await ctx.send(self.bot.babel(ctx, 'help', 'obsolete_command'))
        elif command in re.split(r', |>', self.bot.config['help']['moved_commands']):
          moves = re.split(r', |>', self.bot.config['help']['moved_commands'])
          target = moves.index(command)
          if target % 2 == 0:
            await ctx.send(self.bot.babel(ctx, 'help', 'moved_command', cmd=moves[target + 1]))
        else:
          await ctx.send(self.bot.babel(ctx, 'help', 'no_command'))

    else:
      # show the generic help embed with a variety of featured commands
      embed = discord.Embed(title = f"{self.bot.config['main']['botname']} help",
                            description = self.bot.babel(ctx, 'help', 'introduction',
                                                         longprefix = self.bot.config['main']['prefix_long'],
                                                         videoexamples = self.bot.config.getboolean('help','helpurlvideoexamples'),
                                                         serverinv = self.bot.config['help']['serverinv']),
                            color = int(self.bot.config['main']['themecolor'], 16),
                            url = self.bot.config['help']['helpurl'] if self.bot.config['help']['helpurl'] else None)
      
      sections = self.bot.config['help']['highlight_sections'].split(', ')
      for section in sections:
        hcmds = []
        for hcmd in self.bot.config['help'][section.split()[1]+'_highlights'].split(', '):
          if [l for l in ecommands if hcmd in l]:
            hcmds.append(hcmd)
          else:
            hcmds.append(hcmd+'❌')
        embed.add_field(name = section, value = '```'+', '.join(hcmds)+'```', inline = False)

      embed.set_footer(text = self.bot.babel(ctx, 'help', 'creator_footer'),
                       icon_url = self.bot.user.avatar_url)
      
      await ctx.send(self.bot.babel(ctx, 'help', 'helpurl_cta') if self.bot.config['help']['helpurl'] else "", embed=embed)

  @commands.command(aliases=['info','invite'])
  async def about(self, ctx:commands.Context):
    """information about this bot, including an invite link"""

    embed = discord.Embed(title = self.bot.babel(ctx, 'help', 'about_title'),
                          description = self.bot.babel(ctx, 'help', 'bot_description'),
                          color = int(self.bot.config['main']['themecolor'], 16),
                          url = self.bot.config['help']['helpurl'] if self.bot.config['help']['helpurl'] else None)
    
    embed.add_field(name = self.bot.babel(ctx, 'help', 'about_field1_title'),
                    value = self.bot.babel(ctx, 'help', 'about_field1_value', cmds=len(self.bot.commands), guilds=len(self.bot.guilds)),
                    inline = False)
    embed.add_field(name = self.bot.babel(ctx, 'help', 'about_field2_title'),
                    value = self.bot.babel(ctx, 'help', 'about_field2_value', longprefix=self.bot.config['main']['prefix_long']),
                    inline = False)
    embed.add_field(name = self.bot.babel(ctx, 'help', 'about_field3_title'),
                    value = self.bot.babel(ctx, 'help', 'about_field3_value', videoexamples=self.bot.config.getboolean('help','helpurlvideoexamples'), serverinv=self.bot.config['help']['serverinv']),
                    inline = False)
    embed.add_field(name = self.bot.babel(ctx, 'help', 'about_field4_title'),
                    value = self.bot.babel(ctx, 'help', 'about_field4_value'),
                    inline = False)
    embed.add_field(name = self.bot.babel(ctx, 'help', 'about_field5_title'),
                    value = self.bot.babel(ctx, 'help', 'about_field5_value', invite='https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=0'),
                    inline = False)
    
    embed.set_footer(text = self.bot.babel(ctx, 'help', 'creator_footer'),
                       icon_url = self.bot.user.avatar_url)

    await ctx.send(self.bot.babel(ctx, 'help', 'helpurl_cta') if self.bot.config['help']['helpurl'] else "", embed=embed)

  @commands.command(aliases=['changelog','change'])
  async def changes(self, ctx:commands.Context, ver=None):
    """changes [version]
    list of changes made to this bot since the most recent update (or a version you specify)
    [version] defaults to the latest version if the version you specify isn't found"""
    changes = self.bot.config['help']['changelog'].splitlines()
    fchanges = ["**"+i.replace('> ','')+"**" if i.startswith('> ') else i for i in changes]
    versions = {v.replace('> ',''):i for i,v in enumerate(changes) if v.startswith('> ')}
    versionlist = list(versions.keys())
    if ver == None or ver.replace('v','') not in versionlist: ver = self.bot.config['main']['ver']
    if ver not in versionlist: ver = versionlist[-1]

    start = versions[ver]
    end = start + 15
    changelog = '\n'.join(fchanges[start:end])
    if end < len(fchanges): changelog += "\n..."

    logurl = self.bot.config['help']['helpurl']+"changes.html#"+ver.replace('.','') if self.bot.config['help']['helpurl'] else None

    embed = discord.Embed(title = f"changelog for {self.bot.config['main']['botname']}",
                          description = f"list of changes from v{ver}:\n\n{changelog}",
                          color = int(self.bot.config['main']['themecolor'], 16),
                          url = logurl)
    embed.set_footer(text = f"{self.bot.config['main']['botname']} v{self.bot.config['main']['ver']} created by {self.bot.config['main']['creator']}",
                     icon_url = self.bot.user.avatar_url)
    
    await ctx.send(f"view the full changelog online: ({logurl})" if logurl else None, embed=embed)

  @commands.command()
  async def feedback(self, ctx:commands.Context, feedback:str):
    """feedback (your feedback)
    send feedback directly to the developer(s)"""
    if self.bot.config['help']['feedbackchannel']:
      feedbackchannel = await self.bot.fetch_channel(self.bot.config['help']['feedbackchannel'])
      if feedbackchannel:
        embed = discord.Embed(title = f"feedback from {ctx.author.name}#{ctx.author.discriminator} in {ctx.guild.name}",
                              description = feedback,
                              color = int(self.bot.config['main']['themecolor'], 16))
        await feedbackchannel.send(embed=embed)
        await ctx.send("your feedback was sent successfully! you may be reached out to in DMs for further information."+\
                        f"\n*you can always join the support server ({self.bot.config['help']['serverinv']}) to get help or give feedback more directly.*" if self.bot.config['help']['serverinv'] else '')
      else:
        await ctx.send("feedback doesn't appear to currently be working, please try again later."+\
                       f"\n*you can always join the support server ({self.bot.config['help']['serverinv']}) to get help or give feedback more directly.*" if self.bot.config['help']['serverinv'] else '')
    else:
      await ctx.send(f"please join the support server ({self.bot.config['help']['serverinv']}) to get help or give feedback more directly." if self.bot.config['help']['serverinv']\
                     else f"{self.bot.config['main']['botname']} doesn't currently have a method for recieving feedback or providing support, please check back later.")

def setup(bot):
  bot.add_cog(Help(bot))