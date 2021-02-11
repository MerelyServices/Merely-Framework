from discord import Intents
from discord.ext import commands 
from .config import Config
import sys, time, os

#stdout to file
if not os.path.exists(globals.store+'logs'): os.makedirs(globals.store+'logs')
class Logger(object):
	def __init__(self,err=False):
		self.terminal = sys.stdout
		self.err = err
	def write(self, message):
		self.terminal.write(message.encode('utf-8').decode('ascii','ignore'))
		with open(globals.store+"logs/merely"+('-errors' if self.err else '')+"-"+globals.ver+"-"+time.strftime("%d-%m-%y")+".log", "a", encoding='utf-8') as log:
			log.write(message)
	def flush(self):
		return self

sys.stdout = Logger()
sys.stderr = Logger(err=True)

config = Config()

intents = Intents.none()
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
# intents.reactions = True
# intents.guild_reactions
# intents.dm_reactions
intents.typing = False
# intents.guild_typing
# intents.dm_typing


bot = commands.Bot(command_prefix=config['main']['prefix'])
bot.config = config
bot.remove_command('help')