"""
  Help - User support and documentation
  Features: data-driven formatting based on config and translation files
  Recommended cogs: any cogs that have featured commands
"""

from __future__ import annotations

import re
from typing import Union, Optional, TYPE_CHECKING
import disnake
from disnake.ext import commands

if TYPE_CHECKING:
  from ..main import MerelyBot
  from ..babel import Resolvable


class Help(commands.Cog):
  """ User friendly, semi-automated, documentation """
  SCOPE = 'help'

  @property
  def config(self) -> dict[str, str]:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)
    if 'customstatus' not in self.config:
      self.config['customstatus'] = ''
    if 'helpurl' not in self.config:
      self.config['helpurl'] = ''
    if 'codeurl' not in self.config:
      self.config['codeurl'] = ''
    if 'helpurlvideoexamples' not in self.config:
      self.config['helpurlvideoexamples'] = ''
    if 'serverinv' not in self.config:
      self.config['serverinv'] = ''
    if 'feedbackchannel' not in self.config:
      self.config['feedbackchannel'] = ''
    if 'highlight_sections' not in self.config:
      self.config['highlight_sections'] = '💡 learn'
    if 'learn_highlights' not in self.config:
      self.config['learn_highlights'] = self.SCOPE
    if 'future_commands' not in self.config:
      self.config['future_commands'] = ''
    if 'obsolete_commands' not in self.config:
      self.config['obsolete_commands'] = ''
    if 'hidden_commands' not in self.config:
      self.config['hidden_commands'] = ''
    if 'changelog' not in self.config:
      self.config['changes'] = '> '+bot.config['main']['ver']+'\n- No changes yet!'

  @commands.Cog.listener('on_connect')
  async def on_starting(self):
    """ make the bot appear busy if it isn't ready to handle commands """
    if not self.bot.is_ready():
      await self.bot.change_presence(status=disnake.Status.dnd)

  @commands.Cog.listener('on_ready')
  async def set_status(self, status:disnake.Status = None, message:str = None):
    """ appear online and add help command information to the status """
    if message is None:
      if self.config['customstatus']:
        message = self.config['customstatus']
      else:
        message = self.bot.config['main']['prefix_short']+'help'
    status = disnake.Status.online if status is None else status
    activity = disnake.Game(message)
    await self.bot.change_presence(status=status, activity=activity)

  def find_command(self, command:str) -> Union[commands.Command, commands.InvokableSlashCommand]:
    """ search currently enabled commands for an instance of the string """
    for cmd in self.bot.slash_commands:
      if command == cmd.name:
        return cmd
    for cmd in self.bot.commands:
      if command == cmd.name or command in cmd.aliases:
        return cmd
    return None

  def get_docs(self, ctx:Union[commands.Context, disnake.CommandInteraction], cmd:str):
    """ find documentation for this command in babel """
    matchedcommand = self.find_command(cmd)
    # return usage information for a specific command
    if matchedcommand:
      reslang = self.bot.babel.resolve_lang(
        ctx.author.id, ctx.guild.id, ctx if isinstance(ctx, disnake.Interaction) else None
      )
      for reflang in reslang:
        reflang = self.bot.babel.langs[reflang]
        for key in reflang.keys():
          if f'command_{matchedcommand.name}_help' in reflang[key]:
            docsrc = (
              self.bot.babel(ctx, key, f'command_{matchedcommand.name}_help', cmd=cmd)
              .splitlines()
            )
            if isinstance(matchedcommand, commands.InvokableSlashCommand):
              docs = f"**{docsrc[0].replace(self.bot.config['main']['prefix_short'], '/')}**"
            else:
              docs = f'**{docsrc[0]}**'
            if len(docsrc) > 1:
              docs += '\n'+docsrc[1]
            if len(docsrc) > 2:
              for line in docsrc[2:]:
                docs += '\n*'+line+'*'
            return docs
    return None

  @commands.slash_command(name='help')
  async def slash_help(
    self, inter:disnake.CommandInteraction, command:Optional[str] = None
  ):
    """
    Learn how to use this bot

    Parameters
    ----------
    command: Search for a specific command's documentation
    """
    await self.help(inter, command)

  @commands.command(aliases=['?','??'])
  async def help(
    self,
    ctx:Union[commands.Context, disnake.CommandInteraction],
    command:Optional[str] = None,
    **kwargs
  ):
    """finds usage information in babel and sends them
    highlights some commands if command is None"""

    if command:
      docs = self.get_docs(ctx, command)
      if docs is not None:
        # we found the documentation
        await ctx.send(docs, **kwargs)
      elif self.find_command(command) is not None:
        # the command definitely exists, but there's no documentation
        await ctx.send(self.babel(ctx, 'no_docs'), **kwargs)
      else:
        # the command doesn't exist right now, figure out why.
        if command in self.config['future_commands'].split(', '):
          # this command will be coming soon according to config
          await ctx.send(self.babel(ctx, 'future_command'), **kwargs)
        elif command in self.config['obsolete_commands'].split(', '):
          # this command is obsolete according to config
          await ctx.send(self.babel(ctx, 'obsolete_command'), **kwargs)
        elif command in re.split(r', |>', self.config['moved_commands']):
          # this command has been renamed and requires a new syntax
          moves = re.split(r', |>', self.config['moved_commands'])
          target = moves.index(command)
          if target % 2 == 0:
            await ctx.send(self.babel(ctx, 'moved_command', cmd=moves[target + 1]), **kwargs)
          else:
            print(
              "WARNING: bad config. in help/moved_command:\n"
              f"{moves[target-1]} is now {moves[target]} but {moves[target]} doesn't exist."
            )
            await ctx.send(self.babel(ctx, 'no_command'), **kwargs)
        else:
          await ctx.send(self.babel(ctx, 'no_command'), **kwargs)

    else:
      # show the generic help embed with a variety of featured commands
      longprefix = self.bot.config['main']['prefix_long']
      if 'Prefix' in self.bot.cogs:
        if isinstance(ctx.channel, disnake.TextChannel) and\
          str(ctx.channel.guild.id) in self.bot.config['prefix'] and\
          len(self.bot.config['prefix'][str(ctx.channel.guild.id)]):
          longprefix = None
      embed = disnake.Embed(
        title=self.babel(ctx, 'title'),
        description=self.babel(
          ctx, 'introduction',
          longprefix=longprefix,
          videoexamples=bool(self.config['helpurlvideoexamples']),
          serverinv=self.config['serverinv']
        ),
        color=int(self.bot.config['main']['themecolor'], 16),
        url=self.config['helpurl'] if self.config['helpurl'] else '')

      sections = self.config['highlight_sections'].split(', ')
      for section in sections:
        hcmds = []
        for hcmd in self.config[section.split()[1]+'_highlights'].split(', '):
          if self.find_command(hcmd):
            hcmds.append(hcmd)
          else:
            hcmds.append(hcmd+'❌')
        embed.add_field(
          name=section, value='```'+self.bot.babel.string_list(ctx, hcmds)+'```', inline=False
        )

      embed.set_footer(text=self.babel(ctx, 'creator_footer'),
                       icon_url=self.bot.user.avatar.url)

      await ctx.send(
        self.babel(ctx, 'helpurl_cta') if self.config['helpurl'] else "",
        embed=embed,
        **kwargs
      )

  @slash_help.autocomplete('command')
  def ac_command(self, _:disnake.CommandInteraction, command:str):
    """ find any commands that contain the provided string """
    matches = []
    hide = self.bot.config.get(self.SCOPE, 'hidden_commands', fallback='').split(', ')
    for cmd in self.bot.slash_commands:
      if command in cmd.name and cmd.name not in matches and cmd.name not in hide:
        matches.append(cmd.name)
    for cmd in self.bot.commands:
      if command in cmd.name and cmd.name not in matches and cmd.name not in hide:
        matches.append(cmd.name)
      else:
        for alias in cmd.aliases:
          if command in alias and cmd.name not in matches and cmd.name not in hide:
            matches.append(cmd.name)
    return matches[0:25]

  @commands.slash_command()
  async def about(self, inter:disnake.CommandInteraction):
    """
    General information about this bot, including an invite link
    """

    embed = disnake.Embed(
      title=self.babel(inter, 'about_title'),
      description=self.babel(inter, 'bot_description'),
      color=int(self.bot.config['main']['themecolor'], 16),
      url=self.config['helpurl'] if self.config['helpurl'] else ''
    )

    embed.add_field(
      name=self.babel(inter, 'about_field1_title'),
      value=self.babel(
        inter,
        'about_field1_value',
        cmds=len(self.bot.application_commands),
        guilds=len(self.bot.guilds)
      ),
      inline=False
    )
    embed.add_field(
      name=self.babel(inter, 'about_field2_title'),
      value=self.babel(
        inter,
        'about_field2_value',
        longprefix=self.bot.config['main']['prefix_long']
      ),
      inline=False
    )
    embed.add_field(
      name=self.babel(inter, 'about_field3_title'),
      value=self.babel(
        inter,
        'about_field3_value',
        videoexamples=bool(self.config['helpurlvideoexamples']),
        serverinv=self.config['serverinv']
      ),
      inline=False
    )
    embed.add_field(
      name=self.babel(inter, 'about_field4_title'),
      value=self.babel(inter, 'about_field4_value'),
      inline=False
    )
    embed.add_field(
      name=self.babel(inter, 'about_field5_title'),
      value=self.babel(
        inter,
        'about_field5_value',
        invite=(
          'https://discord.com/oauth2/authorize?client_id=' +
          str(self.bot.user.id) +
          '&scope=bot%20applications.commands&permissions=0'
        )
      ),
      inline=False
    )

    embed.set_footer(
      text=self.babel(inter, 'creator_footer'),
      icon_url=self.bot.user.avatar.url
    )

    await inter.send(
      self.babel(inter, 'helpurl_cta') if self.config['helpurl'] else "",
      embed=embed
    )

  @commands.slash_command()
  async def changes(self, inter:disnake.CommandInteraction, search:Optional[str] = None):
    """
    See what's changed in recent updates

    Parameters
    ----------
    search: Find the version a change occured in, or search for a version number
    """
    changes = self.config['changelog'].splitlines()
    fchanges = ["**"+i.replace('> ','')+"**" if i.startswith('> ') else i for i in changes]
    versions = {v.replace('> ',''):i for i,v in enumerate(changes) if v.startswith('> ')}
    versionlist = list(versions.keys())
    if search is None or search.replace('v','') not in versionlist:
      search = self.bot.config['main']['ver']
    if search not in versionlist: # if config-defined version has no changelog
      search = versionlist[-1]

    start = versions[search]
    end = start + 15
    changelog = '\n'.join(fchanges[start:end])
    if end < len(fchanges):
      changelog += "\n..."

    logurl = (
      self.config['helpurl']+"changes.html#"+search.replace('.','') if self.config['helpurl'] else ''
    )

    embed = disnake.Embed(
      title=self.babel(inter, 'changelog_title'),
      description=(
        self.babel(inter, 'changelog_description', ver=search) +
        '\n\n' + changelog
      ),
      color=int(self.bot.config['main']['themecolor'], 16),
      url=logurl
    )
    embed.set_footer(
      text=self.babel(inter, 'creator_footer'),
      icon_url=self.bot.user.avatar.url
    )

    await inter.send(
      self.babel(inter, 'changelog_cta', logurl=logurl) if logurl else None,
      embed=embed
    )

  @changes.autocomplete('search')
  def ac_version(self, _:disnake.CommandInteraction, search:str):
    """ find any matching versions """
    matches = []
    iver = '0'
    for line in self.config['changelog'].splitlines():
      if line.startswith('> '):
        iver = line[2:]
      if search.lower() in line.lower() and iver not in matches:
        matches.append(iver)

    if len(matches) > 25:
      matches = [matches[0], '...'] + matches[len(matches) - 23:]
    return matches


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(Help(bot))
