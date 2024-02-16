"""
  MerelyBot Framework
  Adds modularity, translation support, and a config system to Python Discord bots
  Created by Yiays and contributors
"""

import sys, time, os, re
from itertools import groupby
from glob import glob
import disnake
from disnake.ext import commands
from config import Config
from babel import Babel


class MerelyBot(commands.AutoShardedBot):
  """
    An extension of disnake.commands.AutoShardedBot with added features

    This includes a babel module for localised strings, a config module, automatic extension
    loading, config-defined intents, config-defined prefixes, and logging.
  """
  config:Config
  babel:Babel
  verbose = False
  member_cache = True
  overlay = False

  def __init__(self, **kwargs):
    if os.path.exists('overlay'):
      overlayconfpath = os.path.join('overlay', 'config')
      overlaybabelpath = os.path.join('overlay', 'babel')
      self.overlay = True
      if os.path.exists(overlayconfpath):
        print("Using 'overlay/config/'")
        self.config = Config(overlayconfpath)
      else:
        self.config = Config()
      if os.path.exists(overlaybabelpath):
        print("Using 'overlay/babel/'")
        self.babel = Babel(self.config, overlaybabelpath)
    else:
      self.config = Config()
      self.babel = Babel(self.config)

    print(f"""
    merely framework{
      ' beta' if self.config.getboolean('main', 'beta') else ''
    } v{self.config['main']['ver']}
    currently named {self.config['main']['botname']} by config, uses {
      self.config['main']['prefix_short']
    }
    created by Yiays#5930. https://github.com/yiays/merelybot
    """)

    #stdout to file
    if not os.path.exists('logs'):
      os.makedirs('logs')
    sys.stdout = Logger()
    sys.stderr = Logger(err=True)

    if 'verbose' in kwargs:
      self.verbose = kwargs['verbose']

    # set intents
    intents = disnake.Intents.none()
    intents.guilds = self.config.getboolean('intents', 'guilds')
    intents.members = self.config.get('intents', 'members') != 'none'
    intents.moderation = self.config.getboolean('intents', 'moderation')
    intents.emojis = self.config.getboolean('intents', 'emojis')
    intents.integrations = self.config.getboolean('intents', 'integrations')
    intents.webhooks = self.config.getboolean('intents', 'webhooks')
    intents.invites = self.config.getboolean('intents', 'invites')
    intents.voice_states = self.config.getboolean('intents', 'voice_states')
    intents.presences = self.config.getboolean('intents', 'presences')
    intents.message_content = self.config.getboolean('intents', 'message_content')
    intents.guild_messages = 'guild' in self.config.get('intents', 'messages')
    intents.dm_messages = 'dm' in self.config.get('intents', 'messages')
    intents.messages = intents.guild_messages or intents.dm_messages
    intents.guild_reactions = 'guild' in self.config.get('intents', 'reactions')
    intents.dm_reactions = 'dm' in self.config.get('intents', 'reactions')
    intents.reactions = intents.guild_reactions or intents.dm_reactions
    intents.guild_typing = 'guild' in self.config.get('intents', 'typing')
    intents.dm_typing = 'dm' in self.config.get('intents', 'typing')
    intents.typing = intents.guild_typing or intents.dm_typing

    # set cache policy
    cachepolicy = disnake.MemberCacheFlags.from_intents(intents)
    if self.config.get('intents', 'members') in ('uncached', 'False'):
      cachepolicy = disnake.MemberCacheFlags.none()
      self.member_cache = False

    # set sync policy
    syncflags = commands.CommandSyncFlags.default()
    if self.verbose:
      syncflags.sync_commands_debug = True

    super().__init__(
      command_prefix=self.check_prefix if intents.message_content else None,
      help_command=None,
      intents=intents,
      member_cache_flags=cachepolicy,
      command_sync_flags=syncflags,
      case_insensitive=True
    )

    self.autoload_extensions()

  def check_prefix(self, _, msg:disnake.Message) -> list[str]:
    """ Check provided message should trigger the bot """
    if (
      self.config['main']['prefix_short'] and
      msg.content.lower().startswith(self.config['main']['prefix_short'].lower())
    ):
      return (
        [
          msg.content[0: len(self.config['main']['prefix_short'])],
          msg.content[0: len(self.config['main']['prefix_short'])] + ' '
        ]
      )
    if (
      self.config['main']['prefix_long'] and
      msg.content.lower().startswith(self.config['main']['prefix_long'].lower())
    ):
      return msg.content[0:len(self.config['main']['prefix_long'])] + ' '
    return commands.when_mentioned(self, msg)

  def autoload_extensions(self):
    """ Search the filesystem for extensions, list them in config, load them if enabled """
    # a natural sort is used to make it possible to prioritize extensions by filename
    # add underscores to extension filenames to increase their priority
    extsearch = os.path.join('extensions', '*.py')
    extoverlaysearch = os.path.join('overlay', 'extensions', '*.py')
    overlay_extensions = []
    if os.path.exists(extoverlaysearch):
      print("Using 'overlay/extensions/'")
      overlay_extensions = glob(extoverlaysearch)
    for extpath in sorted(
      list(set(overlay_extensions + glob(extsearch))),
      key=lambda s:[
        int(''.join(g)) if k else ''.join(g) for k,g in groupby('\0'+s, str.isdigit)
      ]
    ):
      extfile = re.sub(r'^(extensions[/\\]|overlay[/\\]extensions[/\\])', '', extpath)[:-3]
      extname = extfile.strip('_')
      if extname in self.config['extensions'].keys():
        if self.config.getboolean('extensions', extname):
          try:
            self.load_extension(
              'overlay.extensions.'+extfile if extpath.startswith('overlay')
              else 'extensions.'+extfile
            )
            print(f"{extname} loaded." + (' (overlay)' if extpath.startswith('overlay') else ''))
          except Exception as e:
            print(f"Failed to load extension '{extpath[:-3]}':\n{e}")
        else:
          if self.verbose:
            print(f"{extname} is disabled, skipping.")
      else:
        self.config['extensions'][extname] = 'False'
        print(f"discovered {extname}, disabled by default, you can enable it in the config.")
    self.config.save()


class Logger(object):
  """ Records all stdout and stderr to log files, filename is based on date """
  def __init__(self, err=False):
    self.terminal = sys.stderr if err else sys.stdout
    self.err = err

  def write(self, message):
    """ Write output to log file """
    mfolder = os.path.join('logs', time.strftime("%m-%y"))
    if not os.path.exists(mfolder):
      os.makedirs(mfolder)
    self.terminal.write(message.encode('utf-8').decode('ascii','ignore'))
    fname = os.path.join(
      "logs",
      time.strftime("%m-%y"),
      "merelybot"+('-errors' if self.err else '')+"-"+time.strftime("%d-%m-%y")+".log"
    )
    with open(fname, "a", encoding='utf-8') as log:
      log.write(message)

  def flush(self):
    """ This is here just to keep the writable requirement of stdout and stderr happy """
    self.terminal.flush()
    return self


if __name__ == '__main__':
  if set(['-h','--help']) & set(sys.argv):
    print("""
    merelybot commands
    -h,--help		shows this help screen
    -v,--verbose		enables verbose logging
    """)
  else:
    bot = MerelyBot(verbose=bool(set(['-v','--verbose']) & set(sys.argv)))

    token = bot.config.get('main', 'token', fallback=None)
    if token:
      bot.run(token)
    else:
      raise Exception(
        "Invalid token!" +
        "\nGet a token from https://discordapp.com/developers/applications/ and put it in config.ini"
      )

print("exited.")
