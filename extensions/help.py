"""
  Help - User support and documentation
  Features: data-driven formatting based on config and translation files
  Recommended cogs: any cogs that have featured commands
"""

from __future__ import annotations

import re, asyncio
from typing import Optional, TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


class Help(commands.Cog):
  """ User friendly, semi-automated, documentation """
  SCOPE = 'help'

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
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
    if 'changelogurl' not in self.config:
      self.config['changelogurl'] = ''
    if 'codeurl' not in self.config:
      self.config['codeurl'] = ''
    if 'helpurlvideoexamples' not in self.config:
      self.config['helpurlvideoexamples'] = ''
    if 'serverinv' not in self.config:
      self.config['serverinv'] = ''
    if 'highlight_sections' not in self.config:
      self.config['highlight_sections'] = '💡 learn'
      if 'learn_highlights' not in self.config:
        self.config['learn_highlights'] = 'help'
    if 'future_commands' not in self.config:
      self.config['future_commands'] = ''
    if 'obsolete_commands' not in self.config:
      self.config['obsolete_commands'] = ''
    if 'hidden_commands' not in self.config:
      self.config['hidden_commands'] = ''
    if 'moved_commands' not in self.config:
      self.config['moved_commands'] = ''
    if 'changelog' not in self.config:
      self.config['changelog'] = '> '+bot.config['main']['ver']+'\n- No changes yet!'
    elif (
      bot.config.reference and
      bot.config.reference['help']['changelog'] != self.config['changelog']
    ):
      self.config['changelog'] = bot.config.reference['help']['changelog']
      self.config['future_commands'] = bot.config.reference['help']['future_commands']
      self.config['obsolete_commands'] = bot.config.reference['help']['obsolete_commands']
      self.config['moved_commands'] = bot.config.reference['help']['moved_commands']
      bot.config.save()
      print("   - Updated changelog, future_commands, obsolete_commands, and moved_commands")

  @commands.Cog.listener('on_connect')
  async def on_starting(self):
    """ make the bot appear busy if it isn't ready to handle commands """
    if not self.bot.is_ready():
      await self.bot.change_presence(status=discord.Status.dnd)

  @commands.Cog.listener('on_ready')
  async def set_status(self, status:discord.Status = None, message:str = None):
    """ appear online and add help command information to the status """
    if message is None:
      if self.config['customstatus']:
        message = self.config['customstatus']
      else:
        message = '/help'
    status = discord.Status.online if status is None else status
    activity = discord.Game(message)
    await asyncio.sleep(1) # Add delay to reduce flood of requests on connect
    await self.bot.change_presence(status=status, activity=activity)

  def find_command(self, search:str) -> app_commands.Command:
    """ search currently enabled commands for an instance of the string """
    splitsearch = None
    if ' ' in search:
      splitsearch = search.split()
    for cmd in self.bot.tree.walk_commands():
      if search == cmd.name:
        return cmd
      if splitsearch and isinstance(cmd, app_commands.Group):
        if splitsearch[0] == cmd.name and splitsearch[1] in (sc.name for sc in cmd.commands):
          return [sc for sc in cmd.commands if sc.name == splitsearch[1]][0]
    return None

  def get_docs(self, inter:discord.Interaction, command:app_commands.Command):
    """ find documentation for this command in babel """
    reslang = self.bot.babel.resolve_lang(
      inter.user.id, inter.guild.id if inter.guild else None, inter
    )
    commandname = (command.root_parent.name + ' ' if command.root_parent else '') + command.name
    for reflang in reslang:
      reflang = self.bot.babel.langs[reflang]
      for key in reflang.keys():
        if f"command_{commandname.replace(' ', '_')}_help" in reflang[key]:
          docsrc = (
            self.bot.babel(
              inter, key, f"command_{commandname.replace(' ', '_')}_help", cmd=commandname
            ).splitlines()
          )
          docs = f'**{docsrc[0]}**'
          if len(docsrc) > 1:
            docs += '\n'+docsrc[1]
          if len(docsrc) > 2:
            for line in docsrc[2:]:
              docs += '\n*'+line+'*'
          return docs
    # Return the docstring otherwise
    mentionline = (
      f'**{self.bot.babel.mention_command(command.name)}' + (' ' if command.parameters else '')
    )
    autodoc = command.description + ('\n' if command.parameters else '')
    for param in command.parameters:
      mentionline += f'({param.name})' if param.required else f'[{param.name}]'
      autodoc += '\n' + f'*{param.name}: {param.description}*'
    return mentionline + '**\n' + autodoc

  def resolve_docs(self, inter:discord.Interaction, search:str):
    """
      Find documentation for any command
    """
    if command := self.find_command(search):
      docs = self.get_docs(inter, command)
      if docs is not None:
        # we found the documentation
        return docs
    # the command doesn't exist right now, figure out why.
    if search in self.config['future_commands'].split(', '):
      # this command will be coming soon according to config
      return self.babel(inter, 'future_command', cmd=search)
    elif search in self.config['obsolete_commands'].split(', '):
      # this command is obsolete according to config
      return self.babel(inter, 'obsolete_command', cmd=search)
    elif search in re.split(r', |>', self.config['moved_commands']):
      # this command has been renamed and requires a new syntax
      moves = re.split(r', |>', self.config['moved_commands'])
      target = moves.index(search)
      if target % 2 == 0:
        return self.babel(inter, 'moved_command', oldcmd=search, cmd=moves[target + 1])
      else:
        print(
          "WARN: bad config. in help/moved_commands:\n"
          f"{moves[target]} is now {moves[target+1]} but {moves[target+1]} doesn't exist."
        )
        return self.babel(inter, 'no_command', cmd=search)
    elif command:
      # the command definitely exists, but there's no documentation
      return self.babel(inter, 'no_docs', cmd=search)
    else:
      return self.babel(inter, 'no_command', cmd=search)

  @app_commands.command()
  @app_commands.describe(command="Name any command you'd like specific help with")
  async def help(self, inter:discord.Interaction, command:Optional[str]):
    """
      A repository of all the information you should need to use this bot
    """
    if command:
      await inter.response.send_message(self.resolve_docs(inter, command))
      return

    # show the generic help embed with a variety of featured commands
    embed = discord.Embed(
      title=self.babel(inter, 'title'),
      description=self.babel(
        inter,
        'introduction',
        videoexamples=bool(self.config['helpurlvideoexamples']),
        serverinv=self.config['serverinv']
      ),
      color=int(self.bot.config['main']['themecolor'], 16),
      url=self.config['helpurl'] if self.config['helpurl'] else ''
    )

    sections = self.config['highlight_sections'].split(', ')
    for section in sections:
      hcmds = []
      for hcmd in self.config[section.split()[1]+'_highlights'].split(', '):
        cmdstr = self.bot.babel.mention_command(hcmd)
        if self.find_command(hcmd):
          hcmds.append(cmdstr)
        else:
          hcmds.append(cmdstr+'❌')
      embed.add_field(
        name=section, value=self.bot.babel.string_list(inter, hcmds), inline=False
      )

    embed.set_footer(text=self.babel(inter, 'creator_footer'), icon_url=self.bot.user.avatar.url)

    await inter.response.send_message(
      self.babel(inter, 'helpurl_cta') if self.config['helpurl'] else "",
      embed=embed
    )

  @help.autocomplete('command')
  async def ac_command(self, _:discord.Interaction, search:str):
    """ find any commands that contain the provided string """
    matches = []
    hide = self.config.get('hidden_commands', fallback='').split(', ')
    for cmd in self.bot.tree.walk_commands():
      if search in cmd.name and cmd.name not in hide:
        commandname = (cmd.root_parent.name + ' ' if cmd.root_parent else '') + cmd.name
        matches.append(app_commands.Choice(name=commandname, value=commandname))
    return matches[0:25]

  @app_commands.command()
  async def about(self, inter:discord.Interaction):
    """
    General information about this bot, including an invite link
    """

    embed = discord.Embed(
      title=self.babel(inter, 'about_title'),
      description=self.babel(inter, 'bot_description'),
      color=int(self.bot.config['main']['themecolor'], 16),
      url=self.config['helpurl'] if self.config['helpurl'] else ''
    )

    embed.add_field(
      name=self.babel(inter, 'about_field1_title'),
      value=self.babel(inter, 'about_field1_value',
                       cmds=sum(1 for _ in self.bot.tree.walk_commands()),
                       guilds=len(self.bot.guilds)),
      inline=False
    )
    embed.add_field(
      name=self.babel(inter, 'about_field2_title'),
      value=self.babel(inter, 'about_field2_value'),
      inline=False
    )
    embed.add_field(
      name=self.babel(inter, 'about_field3_title'),
      value=self.babel(inter, 'about_field3_value',
                       videoexamples=self.config.getboolean('helpurlvideoexamples'),
                       serverinv=self.config['serverinv']),
      inline=False
    )
    embed.add_field(
      name=self.babel(inter, 'about_field4_title'),
      value=self.babel(inter, 'about_field4_value'),
      inline=False
    )
    embed.add_field(
      name=self.babel(inter, 'about_field5_title'),
      value=self.babel(inter, 'about_field5_value', invite=(
        'https://discord.com/oauth2/authorize?client_id=' +
        str(self.bot.user.id) +
        '&scope=bot%20applications.commands&permissions=0'
      )),
      inline=False
    )

    embed.set_footer(
      text=self.babel(inter, 'creator_footer'),
      icon_url=self.bot.user.avatar.url
    )

    await inter.response.send_message(
      self.babel(inter, 'helpurl_cta') if self.config['helpurl'] else "",
      embed=embed
    )

  @app_commands.command()
  @app_commands.describe(
    search="Find the version a change occured in, or search for a version number"
  )
  async def changes(self, inter:discord.Interaction, search:Optional[str] = None):
    """
      See what has changed in recent updates
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

    logurl = self.config['changelogurl'] if self.config['changelogurl'] else ''

    embed = discord.Embed(
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

    await inter.response.send_message(
      self.babel(inter, 'changelog_cta', logurl=logurl) if logurl else None,
      embed=embed
    )

  @changes.autocomplete('search')
  async def ac_version(self, _:discord.Interaction, search:str):
    """ find any matching versions """
    matches = []
    foundver = []
    iver = '0'
    for line in self.config['changelog'].splitlines():
      if line.startswith('> '):
        iver = line[2:]
      if search.lower() in line.lower() and iver not in foundver:
        matches.append(app_commands.Choice(name=iver, value=iver))
        foundver.append(iver)

    ellipse = app_commands.Choice(name='...', value='')
    if len(matches) > 25:
      matches = [matches[0], ellipse] + matches[len(matches) - 23:]
    return matches


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Help(bot))
