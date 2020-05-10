"""
	Merely - created by Yiays#5930
	https://merely.yiays.com
	A Discord bot created to entertian, moderate, and inform.
"""

import os, sys, traceback, asyncio, time, importlib
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
		self.terminal.write(message.encode('utf-8').decode('ascii','ignore'))
		with open(globals.store+"logs/merely"+('-errors' if self.err else '')+"-"+globals.ver+"-"+time.strftime("%d-%m-%y")+".log", "a", encoding='utf-8') as log:
			log.write(message)
	def flush(self):
		return self

sys.stdout = Logger()
sys.stderr = Logger(err=True)

print('starting bot...')

#start commands system
prefixes = [globals.prefix_short, globals.prefix_short+' ']
if len(globals.prefix_long): prefixes.append(globals.prefix_long+' ')

bot=commands.Bot(command_prefix=commands.when_mentioned_or(*prefixes), help_attrs={'enabled':False}, case_insensitive=True)
bot.remove_command('help')

globals.bot=bot

if globals.verbose: print('importing modules...')
if globals.verbose: print('main done!')

# bot command modules
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
	bot.add_cog(meme.Meme(bot, os.environ.get("MemeDB")))
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
	bot.add_cog(tools.Tools(bot, os.environ.get("MemeDB")))
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

if globals.modules['core']:
	class Core(commands.Cog):
		def __init__(self, bot):
			bot = bot
		
		@commands.command(pass_context=True,no_pm=False)
		async def reload(self,ctx,*,modulename:str):
			modulename = modulename.lower()
			if ctx.message.author.id in globals.superusers:
				# if module exists and is enabled
				if modulename in globals.modules and globals.modules[modulename]:
					# edge case module that needs special treatment
					if modulename=='config':
						globals.reload()
						await ctx.message.channel.send("reloaded `config` succesfully!")
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
					
						# - start up the modules again
						
						# modules that need extra parameters
						if modulename in ['meme', 'tools']:
							bot.add_cog(getattr(reloadedmodule, modulename.capitalize())(bot, os.environ.get("MemeDB")))
						# start the module the normal way
						else:
							bot.add_cog(getattr(reloadedmodule, modulename.capitalize())(bot))
						
						# start other components of the module
						if modulename=='webserver':
							asyncio.ensure_future(bot.cogs['Webserver'].start())
					
					except Exception as e:
						print(e)
						await ctx.message.channel.send("failed to reload `"+modulename+"`!")
						return
					
					await ctx.message.channel.send("reloaded `"+modulename+"` succesfully!")
				else:
					await ctx.message.channel.send('`'+modulename+"` isn't available for reloading.")
			else:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","reload")
	bot.add_cog(Core(bot))
	if globals.verbose: print('reload done!')

@bot.event
async def on_connect():
	print('connected!\nlogging in...')

@bot.event
async def on_ready():
	print('logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	
	if not globals.connected:
		if globals.modules['webserver']: asyncio.ensure_future(bot.cogs['Webserver'].start())
		globals.connected=True
	
	if globals.modules['fun']:
		with open(globals.store+"playing.txt","r") as file:
			playing=file.read().split()
		if len(playing)>1:
			print('changing status to '+' '.join(playing)+'...')
			await bot.cogs['Fun'].set_status(playing[0], ' '.join(playing[1:]))
		else:
			print('no playing status found')
			await bot.cogs['Fun'].set_status()
	with open(globals.store+'alive.txt','r') as f:
		try:
			id=int(f.read())
		except:
			id=False
	if id:
		print('informing channel '+str(id)+' of my return...')
		await emformat.genericmsg(bot.get_channel(id),"i have returned.","greet","die")
	if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - **logged in and restored settings.**")
	with open(globals.store+'alive.txt','w') as f:
		f.write('')
	
	if globals.modules['meme']:
		if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - starting background service...")
		try:
			await bot.cogs['Meme'].BackgroundService()
		except Exception as e:
			if globals.logchannel and bot.is_ready(): await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - background service failed to complete!```"+str(e)+"```")
		else:
			if globals.logchannel and bot.is_ready(): await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - background service ended.")

@bot.event
async def on_message(message):
	# determine if the message should be logged and log it
	asyncio.ensure_future(msglog(message))
	# determine if janitor should run on this message and run it
	if globals.modules['admin']:
		asyncio.ensure_future(bot.cogs['Admin'].janitorservice(message))
	# determine if message was posted in a meme channel, and if so determine if it is a meme
	if globals.modules['meme'] and message.channel.id in [m.id for m in globals.memechannels]:
		asyncio.ensure_future(bot.cogs["Meme"].OnMemePosted(message))
	
	ctx = await bot.get_context(message)
	
	# ignore messages that clearly weren't directed at merely
	if ctx.prefix is not None:
		ctx.command = bot.get_command(ctx.invoked_with.lower())
		# detect if the message was recognised as a command
		if ctx.command is None:
			await log("Unknown command: ```"+message.content+"```")
		else:
			await bot.invoke(ctx)

@bot.check_once
async def on_check(ctx):
	# detect if the command was directed at the music bot
	if ctx.command.name == "music":
		if not (globals.musicbuddy and ctx.guild.get_member(globals.musicbuddy) is None):
			# the music bot will handle this one
			return False
	if str(ctx.message.author.id) in globals.lockout:
		if int(globals.lockout[str(ctx.message.author.id)]) > time.time():
			await ctx.message.channel.send(f"you're banned from using this bot for {utils.time_fold(int(globals.lockout[str(ctx.message.author.id)])-time.time())}.")
			return False
		else:
			await ctx.message.channel.send("your ban is over. you may use commands again.")
			globals.lockout.pop(str(ctx.message.author.id),None)
			globals.save()
	return True
	
@bot.event
async def on_guild_join(server):
	if globals.verbose: print(time.strftime("%H:%M:%S",time.localtime())+" - Joined server "+server.name+"!")
	if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - **Joined server *"+server.name+"*!** ["+str(server.id)+"]")
	
	if globals.modules['admin']:
		await bot.cogs['Admin'].send_ownerintro(server)
	
	await bot.change_presence(activity=discord.Game(name=f"{globals.prefix_long} help | {globals.prefix_short}help"))
	if globals.modules['fun']:
		await asyncio.sleep(30)
		with open(globals.store+"playing.txt","r") as file:
			playing=file.read().split(' ')
		if len(playing)>1:
			await bot.cogs['Fun'].set_status(playing[0], ' '.join(playing[1:]))
		else:
			await bot.cogs['Fun'].set_status()

@bot.event
async def on_guild_remove(server):
	if globals.verbose: print(time.strftime("%H:%M:%S",time.localtime())+" - Left server "+server.name+"!")
	if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - **Left server *"+server.name+"*!**")

@bot.event
async def on_member_join(member):
	if member.id == bot.user.id:
		return
	globals.config.read(globals.store+'config.ini')
	if str(member.guild.id) in globals.config.sections() and globals.config.get(str(member.guild.id),'welcome_message') != '':
		await bot.get_channel(int(globals.config.get(str(member.guild.id),'welcome_channel'))).send(globals.config.get(str(member.guild.id),'welcome_message').format('<@!'+str(member.id)+'>',member.guild.name))

@bot.event
async def on_member_remove(member):
	if member.id == bot.user.id:
		return
	globals.config.read(globals.store+'config.ini')
	if str(member.guild.id) in globals.config.sections() and globals.config.get(str(member.guild.id),'farewell_message') != '':
		await bot.get_channel(int(globals.config.get(str(member.guild.id),'farewell_channel'))).send(globals.config.get(str(member.guild.id),'farewell_message').format(member.name+'#'+str(member.discriminator)))

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

async def log(msg:str):
	print(time.strftime("%H:%M:%S",time.localtime())+": "+msg)
	if globals.logchannel:
		await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+": "+msg)

@bot.event
async def on_raw_reaction_add(e):
	if e.channel_id in [m.id for m in globals.memechannels] and e.user_id != bot.user.id:
		await bot.cogs['Meme'].OnReaction(True,e.message_id,e.user_id,e.channel_id,e.emoji)
@bot.event
async def on_raw_reaction_remove(e):
	if e.channel_id in [m.id for m in globals.memechannels]:
		await bot.cogs['Meme'].OnReaction(False,e.message_id,e.user_id)

@bot.event
async def on_error(*args):
	error = traceback.format_exc()
	print(time.strftime("%H:%M:%S",time.localtime())+" - encountered an error;\n"+error)
	# This command tends to be called while the bot is shutting down, stop here.
	if bot.is_closed() or not bot.is_ready():
		return
	if globals.logchannel:
		channel = bot.get_channel(globals.logchannel)
		await channel.send(time.strftime("%H:%M:%S",time.localtime())+" - **encountered an error;**\n```"+truncate(error,1950)+'```')
if globals.verbose: print('events done!')

if __name__ == '__main__':
	if ('Merely' in os.environ and not globals.beta) or ('MerelyBeta' in os.environ and globals.beta):
		print('connecting...')
		bot.run(os.environ.get('Merely' if not globals.beta else 'MerelyBeta'))
	else:
		print('ERROR: you must supply a token as an environment variable before merely can start.')

	#shutdown

	print('exited.')
