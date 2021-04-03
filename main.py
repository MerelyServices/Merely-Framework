import discord
from discord.ext import commands 
from config import Config
import sys, time, os
from itertools import groupby

class merelybot(commands.Bot):
	config = Config()

	intents = discord.Intents.none()
	intents.guilds = config.getboolean('intents', 'guilds')
	intents.members = config.getboolean('intents', 'members')
	intents.bans = config.getboolean('intents', 'bans')
	intents.emojis = config.getboolean('intents', 'emojis')
	intents.integrations = config.getboolean('intents', 'integrations')
	intents.webhooks = config.getboolean('intents', 'webhooks')
	intents.invites = config.getboolean('intents', 'invites')
	intents.voice_states = config.getboolean('intents', 'voice_states')
	intents.presences = config.getboolean('intents', 'presences')
	intents.messages = config.getboolean('intents', 'messages')
	intents.guild_messages = config.getboolean('intents', 'guild_messages')
	intents.dm_messages = config.getboolean('intents', 'dm_messages')
	intents.reactions = config.getboolean('intents', 'reactions')
	intents.guild_reactions = config.getboolean('intents', 'guild_reactions')
	intents.dm_reactions = config.getboolean('intents', 'dm_reactions')
	intents.typing = config.getboolean('intents', 'typing')
	intents.guild_typing = config.getboolean('intents', 'guild_typing')
	intents.dm_typing = config.getboolean('intents', 'dm_typing')

	case_insensitive = True

	def __init__(self):
		print(f"""
		merely framework{' beta' if self.config['main']['beta'] else ''} v{self.config['main']['ver']}
		currently named {self.config['main']['botname']} by config, uses {self.config['main']['prefix_short']}
		created by Yiays#5930. https://github.com/yiays/merelybot
		""")

		#stdout to file
		if not os.path.exists('logs'): os.makedirs('logs')

		sys.stdout = Logger()
		sys.stderr = Logger(err=True)

		prefixes = ()
		if self.config['main']['prefix_short']:
			prefixes += (self.config['main']['prefix_short']+' ', self.config['main']['prefix_short'])
		if self.config['main']['prefix_long']: prefixes += (self.config['main']['prefix_long']+' ')

		super().__init__(command_prefix = commands.when_mentioned_or(*prefixes),
										 help_command = None,
										 intents = self.intents)

		self.autoload_extensions()

	def autoload_extensions(self):
		# a natural sort is used to make it possible to prioritize extensions by filename
		# add underscores to extension filenames to increase their priority
		for ext in sorted(os.listdir('extensions'), key=lambda s:[int(''.join(g)) if k else ''.join(g) for k, g in groupby('\0'+s, str.isdigit)]):
			if ext[-3:] == '.py':
				extfile = ext[:-3]
				extname = extfile.strip('_')
				if extname in self.config['extensions'].keys():
					if self.config.getboolean('extensions', extname):
						try:
							self.load_extension('extensions.'+extfile)
							print(f"{extname} loaded.")
						except Exception as e:
							print(f"Failed to load extension '{ext[:-3]}':\n{e}")
					else:
						if set(['-v','--verbose']) & set(sys.argv): print(f"{extname} is disabled, skipping.")
				else:
					self.config['extensions'][extname] = 'False'
					print(f"discovered {extname}, disabled by default, you can enable it in the config.")
		self.config.save()

class Logger(object):
	def __init__(self, err=False):
		self.terminal = sys.stderr if err else sys.stdout
		self.err = err
	def write(self, message):
		self.terminal.write(message.encode('utf-8').decode('ascii','ignore'))
		with open("logs/merely"+('-errors' if self.err else '')+"-"+time.strftime("%d-%m-%y")+".log", "a", encoding='utf-8') as log:
			log.write(message)
	def flush(self):
		return self

if __name__ == '__main__':
	if set(['-h','--help']) & set(sys.argv):
		print("""
		merelybot commands
		-h,--help		shows this help screen
		-v,--verbose		enables verbose logging
		""")
	else:
		bot = merelybot()
		tokenlabel = 'Merely' if not bot.config.getboolean('main','beta') else 'MerelyBeta'
		token = os.environ.get(tokenlabel)
		if token is not None:
			bot.run(token)
		else:
			raise Exception("failed to login! make sure you provided the correct token using the correct key ({}).".format(tokenlabel))
	
	print("exited.")