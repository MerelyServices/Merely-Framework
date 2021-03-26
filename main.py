import discord
from discord.ext import commands 
from config import Config
import sys, time, os

class merelybot(commands.Bot):
	config = Config()

	intents = discord.Intents.none()
	intents.guilds = True
	intents.members = False
	intents.bans = False
	intents.emojis = False
	intents.integrations = False
	intents.webhooks = False
	intents.invites = False
	intents.voice_states = False
	intents.presences = False
	intents.messages = True
	# intents.guild_messages
	# intents.dm_messages
	intents.reactions = True
	# intents.guild_reactions
	# intents.dm_reactions
	intents.typing = False
	# intents.guild_typing
	# intents.dm_typing

	case_insensitive = True

	def __init__(self):
		print(f"""
		merelybot{' beta' if self.config['main']['beta'] else ''} v{self.config['main']['ver']}
		{"(currently named "+self.config['main']['botname']+" by config)" if self.config['main']['botname'] != 'merelybot' else ''}
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
		for ext in os.listdir('extensions'):
			if ext[-3:] == '.py':
				if ext[:-3] in self.config['extensions'].keys():
					if self.config.getboolean('extensions', ext[:-3]):
						try:
							self.load_extension('extensions.'+ext[:-3])
							print(f"{ext[:-3]} loaded.")
						except Exception as e:
							print(f"Failed to load extension '{ext[:-3]}':\n{e}")
					else:
						if self.config.getboolean('main','verbose'): print(f"Extension {ext[:-3]} is disabled, skipping.")
				else:
					self.config['extensions'][ext[:-3]] = 'False'
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
	bot = merelybot()
	try:
		bot.run(os.environ.get('Merely') if not bot.config.getboolean('main','beta') else os.environ.get('MerelyBeta'))
	except discord.LoginFailure:
		raise Exception("failed to login! make sure you provided the correct token using the correct key.")
	
	print("exited.")