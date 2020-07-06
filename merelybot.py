"""
	Merely - created by Yiays#5930
	https://merely.yiays.com
	A Discord bot created to entertian, moderate, and inform.
	
	merelybot.py is a barebones core to be extended upon with plugins
"""

import os, sys, traceback, asyncio, time, importlib, aiomysql
import discord
from discord.ext import commands
import emformat, globals, utils

#stdout to file
if not os.path.exists(globals.store+'logs'): os.makedirs(globals.store+'logs')
class Logger(object):
	def __init__(self,err=False):
		self.terminal = sys.stdout
		self.err = err
	def write(self, message):
		# Make the directory in case the month changes or a folder was deleted
		if not os.path.exists(globals.store+"logs/"+time.strftime("%m-%y")):
			os.makedirs(globals.store+"logs/"+time.strftime("%m-%y"))
		self.terminal.write(message.encode('utf-8').decode('ascii','ignore'))
		with open(globals.store+"logs/"+time.strftime("%m-%y")+"/merely"+('-errors' if self.err else '')+"-"+globals.ver+"-"+time.strftime("%d-%m-%y")+".log", "a", encoding='utf-8') as log:
			log.write(message)
	def flush(self):
		return self

# Make the directory before changing the logger so errors can be printed if need be.
if not os.path.exists(globals.store+"logs/"+time.strftime("%m-%y")):
	os.makedirs(globals.store+"logs/"+time.strftime("%m-%y"))
sys.stdout = Logger()
sys.stderr = Logger(err=True)

print('starting bot...')

#start commands system
prefixes = [globals.prefix_short, globals.prefix_short+' ']
if len(globals.prefix_long): prefixes.append(globals.prefix_long+' ')

bot=commands.Bot(command_prefix=commands.when_mentioned_or(*prefixes), help_attrs={'enabled':False}, case_insensitive=True)
bot.remove_command('help')

globals.bot=bot
bot.db = None

if globals.verbose: print('setting up events...')
import events
eventmod = events.events(bot)
if globals.verbose: print('events done!')

if globals.verbose: print('importing modules...')

# bot command modules
#core
if globals.modules['core']:
	class Core(commands.Cog):
		def __init__(self, bot):
			bot = bot
		
		@commands.command(no_pm=False)
		async def reload(self,ctx,*,modulename:str):
			modulename = modulename.lower()
			if ctx.author.id in globals.superusers:
				# if module exists and is enabled
				if modulename in globals.modules and globals.modules[modulename]:
					# edge case module that needs special treatment
					if modulename=='config':
						globals.reload()
						await ctx.send("reloaded `config` succesfully!")
						return
					
					if modulename.capitalize() not in bot.cogs:
						await self.load(ctx)
						return
					
					cog = bot.cogs[modulename.capitalize()]
					module = sys.modules[cog.__module__]
					
					# modules that need to be cleaned up before shutting down
					if modulename=='webserver':
						await cog.stop()
					
					try:
						# - reload the module
						reloadedmodule = importlib.reload(module)
						
						# make discord.py refresh the available commands
						bot.remove_cog(modulename.capitalize())
						
						# start the module
						bot.add_cog(getattr(reloadedmodule, modulename.capitalize())(bot))
						
						# start other components of the module
						if modulename=='webserver':
							asyncio.ensure_future(bot.cogs['Webserver'].start())
					
					except Exception as e:
						print(e)
						await ctx.send("failed to reload `"+modulename+"`!")
						return
					
					await ctx.send("reloaded `"+modulename+"` succesfully!")
				else:
					await ctx.send('`'+modulename+"` isn't available for reloading.")
			else:
				await emformat.genericmsg(ctx.channel,"this command is restricted.","error","reload")
		
		@commands.command(no_pm=False)
		async def load(self,ctx,*,modulename:str):
			modulename = modulename.lower()
			if ctx.author.id in globals.superusers:
				# if module exists
				if modulename in globals.modules:
					try:
						# - load the module
						loadedmodule = importlib.import_module(modulename)
						
						# start the module
						bot.add_cog(getattr(loadedmodule, modulename.capitalize())(bot))
						
						# start other components of the module
						if modulename=='webserver':
							asyncio.ensure_future(bot.cogs['Webserver'].start())
					
					except Exception as e:
						print(e)
						await ctx.send("failed to load `"+modulename+"`!")
						return
					
					globals.modules[modulename] = True
					await ctx.send("loaded `"+modulename+"` succesfully!")
				else:
					await ctx.send('`'+modulename+"` isn't available for loading.")
			else:
				await emformat.genericmsg(ctx.channel,"this command is restricted.","error","load")
		
		@commands.command(no_pm=False)
		async def unload(self,ctx,*,modulename:str):
			modulename = modulename.lower()
			if ctx.author.id in globals.superusers:
				# if module exists and is currently in cogs
				if modulename in globals.modules and modulename.capitalize() in bot.cogs:
					# edge case module that needs special treatment
					if modulename in ['config', 'core', 'emformat']:
						await ctx.send('`'+modulename+"` must remain loaded for stability!")
						return
					
					cog = bot.cogs[modulename.capitalize()]
					
					# modules that need to be cleaned up before shutting down
					if modulename=='webserver':
						await cog.stop()
					
					# dereferencing the module and letting gc take care of it
					bot.remove_cog(modulename.capitalize())
					
					del sys.modules[modulename]
					
					globals.modules[modulename] = False
					await ctx.send("unloaded `"+modulename+"` succesfully!")
				else:
					await ctx.send('`'+modulename+"` isn't available for unloading!")
			else:
				await emformat.genericmsg(ctx.channel,"this command is restricted.","error","load")
	
	bot.add_cog(Core(bot))
	if globals.verbose: print('core done!')

# globals
if globals.verbose: print('globals done!')

# emformat
if globals.verbose: print('emformat done!')

#	help
if globals.modules['help']:
	import help
	bot.add_cog(help.Help(bot))
	if globals.verbose: print('help done!')

#	censor
if globals.modules['censor']:
	import censor
	bot.add_cog(censor.Censor(bot))
	if globals.verbose: print('censor done!')

#	fun
if globals.modules['fun']:
	import fun
	bot.add_cog(fun.Fun(bot))
	if globals.verbose: print('fun done!')

#	meme
if globals.modules['meme']:
	import meme
	bot.add_cog(meme.Meme(bot))
	if globals.verbose: print('meme done!')

#	search
if globals.modules['search']:
	import search
	bot.add_cog(search.Search(bot))
	if globals.verbose: print('search done!')

#	admin
if globals.modules['admin']:
	import admin
	bot.add_cog(admin.Admin(bot))
	if globals.verbose: print('admin done!')

#	tools
if globals.modules['tools']:
	import tools
	bot.add_cog(tools.Tools(bot))
	if globals.verbose: print('tools done!')

#	obsolete
if globals.modules['obsolete']:
	import obsolete
	bot.add_cog(obsolete.Obsolete(bot))
	if globals.verbose: print('obsolete done!')

#	webserver
if globals.modules['webserver']:
	import webserver
	bot.add_cog(webserver.Webserver(bot))
	if globals.verbose: print('webserver done!')

# stats
if globals.modules['stats']:
	import stats
	bot.add_cog(stats.Stats(bot))
	if globals.verbose: print('stats done!')

async def onconnect():
	print('connected!')
	
	if "MemeDB" in os.environ:
		if globals.verbose: print('setting up database...')
		bot.meme_db = await aiomysql.create_pool(host='192.168.1.120', port=3306, user='meme', password=os.environ.get('MemeDB'), db='meme', loop=asyncio.get_event_loop())
	else:
		pass #TODO: disable meme and tools, warn the log
bot.events['on_connect'].insert(0, onconnect)

async def ondisconnect():
	print('disconnected!')
	
	if bot.meme_db is not None:
		bot.meme_db.close()
		await bot.meme_db.wait_closed()
		bot.meme_db = None #TODO: There seems to be cases where on_connected isn't fired...
bot.events['on_disconnect'].insert(0, ondisconnect)

async def onready():
	print('logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	
	if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - **logged in and restored settings.**")
bot.events['on_ready'].insert(0,onready)

async def command_handler(message):
	ctx = await bot.get_context(message)
	
	# ignore messages that clearly weren't directed at merely
	if ctx.prefix is not None:
		ctx.command = bot.get_command(ctx.invoked_with.lower())
		# detect if the message was recognised as a command
		if ctx.command is None:
			await log("Unknown command: ```"+message.content+"```")
		else:
			await bot.invoke(ctx)
bot.events['on_message'].insert(0,command_handler)

@bot.check_once
async def on_check(ctx):
	# detect if the command was directed at the music bot
	if ctx.command.name == "music":
		if not (globals.musicbuddy and ctx.guild.get_member(globals.musicbuddy) is None):
			# the music bot will handle this one
			return False
	if str(ctx.author.id) in globals.lockout:
		if int(globals.lockout[str(ctx.author.id)]) > time.time():
			await ctx.send(f"you're banned from using this bot for {utils.time_fold(int(globals.lockout[str(ctx.author.id)])-time.time())}.")
			return False
		else:
			await ctx.send("your ban is over. you may use commands again.")
			globals.lockout.pop(str(ctx.author.id),None)
			globals.save()
	return True
	
async def log_guildjoin(server):
	if globals.verbose: print(time.strftime("%H:%M:%S",time.localtime())+" - Joined server "+server.name+"!")
	if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - **Joined server *"+server.name+"*!** ["+str(server.id)+"]")
	
	await bot.change_presence(activity=discord.Game(name=f"{globals.prefix_long} help | {globals.prefix_short}help"))
	if globals.modules['fun']:
		await asyncio.sleep(30)
		await bot.cogs['Fun'].recover_status()
bot.events['on_guild_join'].insert(0,log_guildjoin)

async def log_guildleave(server):
	if globals.verbose: print(time.strftime("%H:%M:%S",time.localtime())+" - Left server "+server.name+"!")
	if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - **Left server *"+server.name+"*!**")
bot.events['on_guild_remove'].insert(0,log_guildleave)

def truncate(str ,l):
	return (str[:l] + '...') if len(str) > l+3 else str

async def msglog(msg:discord.Message):
	# This command tends to be called while the bot is shutting down, stop it.
	if bot.is_closed() or not bot.is_ready():
		return
	# Determines if message should be logged, and logs it.
	# Criteria for appearing in the log: message isn't in the logchannel, DMs to the bot, messages sent by the bot or the musicbot companion, merely is mentioned or message has a merelybot prefix.
	if msg.channel.id != globals.logchannel and (isinstance(msg.channel,discord.abc.PrivateChannel) or msg.author==bot.user or msg.author.id == globals.musicbuddy or bot.user in msg.mentions or (msg.content.startswith(globals.prefix_long) and len(globals.prefix_long)>0) or msg.content.startswith(globals.prefix_short)):
		if globals.modules['stats']:
			if msg.author==bot.user:
				bot.cogs['Stats'].sentcount+=1
			else:
				bot.cogs['Stats'].recievedcount+=1
		
		content = utils.SanitizeMessage(msg)
		
		# Shorten message to 64 characters
		content=truncate(content,64)
		
		# Strip non-ascii characters for the log
		content_logsafe=content.encode('utf-8').decode('ascii','ignore')
		
		# Either show the server and channel name, or show that this is PMs
		if isinstance(msg.channel,discord.abc.PrivateChannel):
			channel='PM'
		else:
			channel=truncate(msg.guild.name,12)+'#'+truncate(msg.channel.name,12)
		
		embed = None
		if len(msg.embeds)>0:
			embed = msg.embeds[0]
		
		if globals.logchannel:
			await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - ["+channel+"] "+msg.author.name+"#"+msg.author.discriminator+": "+content, embed=embed)
		print(time.strftime("%H:%M:%S",time.localtime())+" - ["+channel+"] "+msg.author.name+"#"+msg.author.discriminator+": "+content_logsafe)
bot.events['on_message'].insert(0,msglog)

async def log(msg:str):
	print(time.strftime("%H:%M:%S",time.localtime())+": "+msg)
	if globals.logchannel:
		await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+": "+msg)

async def log_error(error, *args):
	error = traceback.format_exc()
	print(time.strftime("%H:%M:%S",time.localtime())+" - encountered an error;\n"+error)
	# This command tends to be called while the bot is shutting down, stop here.
	if bot.is_closed() or not bot.is_ready():
		return
	if globals.logchannel:
		channel = bot.get_channel(globals.logchannel)
		await channel.send(time.strftime("%H:%M:%S",time.localtime())+" - **encountered an error;**\n```"+truncate(error,1950)+'```')
bot.events['on_error'].insert(0,log_error)

if __name__ == '__main__':
	if ('Merely' in os.environ and not globals.beta) or ('MerelyBeta' in os.environ and globals.beta):
		print('connecting...')
		bot.run(os.environ.get('Merely' if not globals.beta else 'MerelyBeta'))
	else:
		print('ERROR: you must supply a token as an environment variable before merely can start.')

	#shutdown
	print('exited.')
