import discord
from discord.ext import commands

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
    """help [command]
    highlights some useful commands and explains how to use the prefixes.
    when [command] is provided, specific instructions for a command are provided."""
    
    ecommands = {i:c for i,c in enumerate(self.bot.commands)}
    commandindex = {i: [c.name]+c.aliases for i,c in ecommands.items()}

    if command:
      # return usage information for a specific command
      for i in commandindex.keys():
        if command in commandindex[i]:
          if ecommands[i].help:
            docsrc = ecommands[i].help.splitlines()
            docs = '**'+self.bot.config['main']['prefix_short']+docsrc[0]+'**'
            if len(docsrc) > 1:
              docs += '\n'+docsrc[1]
            if len(docsrc) > 2:
              for line in docsrc[2:]:
                docs += '\n*'+line+'*'
            await ctx.send(docs)
          else:
            await ctx.send("this command doesn't currently have any usage information")
          break
      else:
        if command in self.bot.config['help']['future_commands'].split(', '):
          await ctx.send("this command will be coming in a future update.")
        elif command in self.bot.config['help']['obsolete_commands'].split(', '):
          await ctx.send("this command has been removed. there's no plans to restore it.")
        else:
          await ctx.send("this command either doesn't exist or is currently disabled.")

    else:
      # show the generic help embed with a variety of featured commands
      embed = discord.Embed(title = f"{self.bot.config['main']['botname']} help",
                            description = f"**the prefix is `{self.bot.config['main']['prefix_short']}`.**"+
                                          (f" *you can also use `{self.bot.config['main']['prefix_long']}`.*" if self.bot.config['main']['prefix_long'] else "")+
                                          f"\nget usage info for a command using `{self.bot.config['main']['prefix_short']}help [command]`"+
                                          ("\nyou can also see video examples on the help website!" if self.bot.config.getboolean('help','helpurlvideoexamples') else "")+
                                          (f"\nget dedicated support from the developer and other users on the [support server]({self.bot.config['help']['serverinv']})!" if self.bot.config['help']['serverinv'] else "")+
                                          "\n",
                            color = int(self.bot.config['main']['themecolor'], 16),
                            url = self.bot.config['help']['helpurl'] if self.bot.config['help']['helpurl'] else None)
      
      sections = self.bot.config['help']['highlight_sections'].split(', ')
      for section in sections:
        hcmds = []
        for hcmd in self.bot.config['help'][section.split()[1]+'_highlights'].split(', '):
          if [l for l in commandindex.values() if hcmd in l]:
            hcmds.append(hcmd)
          else:
            hcmds.append(hcmd+'❌')
        embed.add_field(name = section, value = '```'+', '.join(hcmds)+'```', inline = False)

      embed.set_footer(text = f"{self.bot.config['main']['botname']} v{self.bot.config['main']['ver']} created by {self.bot.config['main']['creator']}",
                       icon_url = self.bot.user.avatar_url)
      
      await ctx.send(f"go to {self.bot.config['help']['helpurl']} to learn more!" if self.bot.config['help']['helpurl'] else "", embed=embed)

  @commands.command(aliases=['info','invite'])
  async def about(self, ctx:commands.Context):
    """about
    information about this bot, including an invite link"""

    embed = discord.Embed(title = f"about {self.bot.config['main']['botname']}",
                          description = self.bot.config['main']['description'],
                          color = int(self.bot.config['main']['themecolor'], 16),
                          url = self.bot.config['help']['helpurl'] if self.bot.config['help']['helpurl'] else None)
    
    embed.add_field(name = '✨ features',
                    value = f"{self.bot.config['main']['botname']} has **{len(self.bot.commands)}** commands available to **{len(self.bot.guilds)}** servers.")
    if self.bot.config['main']['prefix_long']:
      embed.add_field(name = '📱 mobile optimized',
                      value = f"{self.bot.config['main']['botname']} is designed to be easy to use on mobile thanks to an optional longer prefix which is easier to type on mobile. (`{self.bot.config['main']['prefix_long']}`)",
                      inline = False)
    embed.add_field(name = '📚 dedicated support',
                    value = f"{self.bot.config['main']['botname']} has a powerful help command where you can get usage information for any command"+
                            (f", a [website]({self.bot.config['help']['helpurl']}) with video examples of how to use commands" if self.bot.config.getboolean('help','helpurlvideoexamples') else '')+
                            (f", and a [support server]({self.bot.config['help']['serverinv']}) where you can get any questions answered or see demos" if self.bot.config['help']['serverinv'] else '')+
                            ".",
                    inline = False)
    embed.add_field(name = "🧩 modular codebase",
                    value = f"{self.bot.config['main']['botname']} is built from the modular *merely framework*, which makes it possible for updates to be released without any interruption and makes it possible for new features to be rolled out rapidly.",
                    inline = False)
    embed.add_field(name = "➕ add to your server",
                    value = f"add {self.bot.config['main']['botname']} to your own server using the following invite link today! https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=0")
    
    embed.set_footer(text = f"{self.bot.config['main']['botname']} v{self.bot.config['main']['ver']} created by {self.bot.config['main']['creator']}",
                     icon_url = self.bot.user.avatar_url)

    await ctx.send(f"go to {self.bot.config['help']['helpurl']} to learn more!" if self.bot.config['help']['helpurl'] else "", embed=embed)

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
  async def feedback(self, ctx:commands.Context, feedback=None):
    """feedback (your feedback)
    send feedback directly to the developer(s)"""
    if self.bot.config['help']['feedbackchannel']:
      feedbackchannel = await self.bot.fetch_channel(self.bot.config['help']['feedbackchannel'])
      if feedbackchannel:
        if feedback is None:
          await self.help(ctx, 'feedback')
          return
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