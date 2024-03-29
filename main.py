"""
  MerelyBot Framework
  Adds modularity, translation support, and a config system to Python Discord bots
  Created by Yiays and contributors
"""

import sys, time, os, re, glob, importlib
from itertools import groupby
from packaging import version
import disnake
from disnake.ext import commands
from config import Config
from babel import Babel
from utilities import Utilities
from auth import Auth


class MerelyBot(commands.AutoShardedInteractionBot):
  """
    An extension of disnake.commands.AutoShardedInteractionBot with added features

    This includes a babel module for localised strings, a config module, automatic extension
    loading, config-defined intents, and logging.
  """
  config:Config
  babel:Babel
  utilities:Utilities = Utilities()
  auth:Auth
  verbose = False
  quiet = False
  load_all_extensions = False
  member_cache = True
  overlay = False
  restart = False

  def __init__(self, **kwargs):
    if 'verbose' in kwargs:
      self.verbose = kwargs['verbose']
    if 'loadall' in kwargs:
      self.load_all_extensions = kwargs['loadall']
    if 'quiet' in kwargs:
      self.quiet = kwargs['quiet']

    if os.path.exists('overlay'):
      overlayconfpath = os.path.join('overlay', 'config')
      overlaybabelpath = os.path.join('overlay', 'babel')
      self.overlay = True
      if os.path.exists(overlayconfpath):
        if not self.quiet:
          print("Loading config\n - Using 'overlay/config/'")
        self.config = Config(overlayconfpath)
      else:
        self.config = Config()
      if os.path.exists(overlaybabelpath):
        if not self.quiet:
          print("Loading translations\n - Using 'overlay/babel/'")
        self.babel = Babel(self.config, overlaybabelpath)
    else:
      self.config = Config(quiet=self.quiet)
      self.babel = Babel(self.config)

    self.auth = Auth(self)

    if not self.quiet:
      print(f"""
      merely framework{
        ' beta' if self.config.getboolean('main', 'beta') else ''
      } v{self.config['main']['ver']}
      currently named {self.config['main']['botname']} by config
      created by Yiays. https://github.com/yiays/merelybot
      """)

    # stdout to file
    if not os.path.exists('logs'):
      os.makedirs('logs')
    if not self.quiet:
      sys.stdout = Logger()
    sys.stderr = Logger(err=True)

    # Migration handling
    if self.config.migrate:
      print(f"Migrating from {self.config.migrate} to {self.config['main']['ver']}...")
      self.automigrate_config()

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
      intents=intents,
      member_cache_flags=cachepolicy,
      command_sync_flags=syncflags
    )

    self.autoload_extensions()

  def reinit(self):
    # Lightweight init that tries to preserve old state
    self.loop = None
    syncflags = commands.CommandSyncFlags.default()
    if self.verbose:
      syncflags.sync_commands_debug = True
    super().__init__(
      intents=self.intents,
      member_cache_flags=(
        disnake.MemberCacheFlags.none() if self.member_cache is None
        else disnake.MemberCacheFlags.from_intents(self.intents)
      ),
      command_sync_flags=syncflags
    )

    self.autoload_extensions()
    print("Bot startup complete\n")

  def autoload_extensions(self):
    """ Search the filesystem for extensions, list them in config, load them if enabled """
    # a natural sort is used to make it possible to prioritize extensions by filename
    # add underscores to extension filenames to increase their priority
    extsearch = os.path.join('extensions', '*.py')
    extoverlaysearch = os.path.join('overlay', 'extensions', '*.py')
    overlay_extensions = []
    if os.path.exists(os.path.join('overlay', 'extensions')):
      if not self.quiet:
        print("Loading extensions\n - Using 'overlay/extensions/'")
      overlay_extensions = glob.glob(extoverlaysearch)
    for extpath in sorted(
      list(set(overlay_extensions + glob.glob(extsearch))),
      key=lambda s:[
        int(''.join(g)) if k else ''.join(g) for k,g in groupby('\0'+s, str.isdigit)
      ]
    ):
      extfile = re.sub(r'^(extensions[/\\]|overlay[/\\]extensions[/\\])', '', extpath)[:-3]
      extname = extfile.strip('_')
      if extname in self.config['extensions'].keys():
        if self.config.getboolean('extensions', extname) or self.load_all_extensions:
          if '_common' in extname and self.load_all_extensions:
            continue # skip *_common extensions as they are not cogs
          try:
            if not self.quiet:
              print(
                f" - Loading {extname}",
                ' (overlay)' if extpath.startswith('overlay') else '',
                sep='',
                end=''
              )
            self.load_extension(
              'overlay.extensions.'+extfile if extpath.startswith('overlay')
              else 'extensions.'+extfile
            )
            if not self.quiet:
              print(" (success)")
          except Exception as e:
            print(f" (failed: '{extpath[:-3]}'):\n{e}")
        else:
          if self.verbose:
            if not self.quiet:
              print(f" - {extname} is disabled, skipping.")
      else:
        self.config['extensions'][extname] = 'False'
        if not self.quiet:
          print(f" - Discovered {extname}, disabled by default, you can enable it in the config.")
    self.config.save()

  def automigrate_config(self):
    """
      Searches the filesystem for migration scripts and applies relevant ones

      Migration files must be in ./migrations, and must start with the target version number (with
      dots replaced with underscores) followed by a final underscore. Then, a brief description of
      what will be changed. For example; 'v1_3_0_help.py'

      If an overlay folder exists, it will also be searched.
    """
    migrations:list[str] = []
    if os.path.exists('migrations'):
      migrations += glob.glob(os.path.join('migrations', 'v*_*.py'))
    if os.path.exists(os.path.join('overlay', 'migrations')):
      print(" - Using 'overlay/migrations'...")
      migrations += glob.glob(os.path.join('overlay', 'migrations', 'v*_*.py'))
    counter = 0
    for migration in migrations:
      fname = migration.split('/')[-1]
      target_ver = version.parse('.'.join(fname.split('_')[:-1]))
      if self.config.migrate <= target_ver <= version.parse(self.config['main']['ver']):
        module = importlib.import_module(re.sub(r'[/\\]', '.', migration[:-3]), 'main')
        module.migrate(self.config)
        counter += 1
    if counter > 0:
      self.config.save()
      print(" - Migration succeeded!")
    else:
      print(" - No migration files found. Skipping...")


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
    """ Flushes the terminal, but not the log file """
    self.terminal.flush()
    return self


if __name__ == '__main__':
  if set(['-h','--help']) & set(sys.argv):
    print("""
    merelybot commands
    -h,--help		    shows this help screen
    -v,--verbose		enables verbose logging
    -q,--quiet      disables general logging
    --loadall       loads all extensions for testing
    """)
  else:
    kwargs = {
      'verbose': bool(set(['-v','--verbose']) & set(sys.argv)),
      'quiet': bool(set(['-q','--quiet']) & set(sys.argv)),
      'loadall': bool(set(['--loadall']) & set(sys.argv))
    }
    bot = MerelyBot(**kwargs)

    token = bot.config.get('main', 'token', fallback=None)
    if token:
      while True:
        try:
          bot.run(token)
          if not bot.restart:
            break
        except Exception as e:
          print("FATAL: Bot crashed. Restarting...\n", e, file=sys.stderr)
        bot.reinit()
    else:
      raise Exception(
        "Invalid token!" +
        "\nGet a token from https://discordapp.com/developers/applications/ and put it in config.ini"
      )
  print("exited.")
