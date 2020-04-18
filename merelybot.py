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
bot=commands.Bot(command_prefix=commands.when_mentioned_or('merely ','m/ ','m/'), help_attrs={'enabled':False}, case_insensitive=True)
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
	globals.modules['help']=help
	bot.add_cog(help.Help(bot))
	if globals.verbose: print('help done!')

#	censor
if globals.modules['censor']:
	import censor
	globals.modules['censor']=censor
	bot.add_cog(censor.Censor(bot))
	if globals.verbose: print('censor done!')

#	fun
if globals.modules['fun']:
	import fun
	globals.modules['fun']=fun
	bot.add_cog(fun.Fun(bot))
	if globals.verbose: print('fun done!')

#	meme
if globals.modules['meme']:
	import meme
	globals.memedbpass=os.environ.get("MemeDB")
	globals.modules['meme']=meme
	globals.meme = meme.Meme(bot)
	bot.add_cog(globals.meme)
	if globals.verbose: print('meme done!')

#	search
if globals.modules['search']:
	import search
	globals.modules['search']=search
	bot.add_cog(search.Search(bot))
	if globals.verbose: print('search done!')

#	admin
if globals.modules['admin']:
	import admin
	globals.modules['admin']=admin
	bot.add_cog(admin.Admin(bot))
	if globals.verbose: print('admin done!')

#	tools
if globals.modules['tools']:
	import tools
	globals.modules['tools']=tools
	bot.add_cog(tools.Tools(bot))
	if globals.verbose: print('tools done!')

#	obsolete
if globals.modules['obsolete']:
	import obsolete
	globals.modules['obsolete']=obsolete
	bot.add_cog(obsolete.Obsolete(bot))
	if globals.verbose: print('obsolete done!')

#	webserver
if globals.modules['webserver']:
	import webserver
	globals.modules['webserver']=webserver
	if globals.verbose: print('webserver done!')

# stats
if globals.modules['stats']:
	import stats
	globals.modules['stats']=stats
	globals.stats=stats.Stats(bot)
	bot.add_cog(globals.stats)
	if globals.verbose: print('stats done!')

if globals.modules['reload']:
	class Reload(commands.Cog):
		def __init__(self, bot):
			bot = bot
		@commands.command(pass_context=True,no_pm=False)
		async def reload(self,ctx,*,module:str):
			if ctx.message.author.id in globals.superusers:
				if module in globals.modules and globals.modules[module]:
					if module=='webserver':
						await globals.modules['webserver'].stop()
						webserver=importlib.reload(globals.modules['webserver'])
						globals.modules['webserver']=webserver
						await webserver.start()
						await ctx.message.channel.send("reloaded `webserver` succesfully!")
					elif module=='config':
						globals.reload()
						await ctx.message.channel.send("reloaded `config` succesfully!")
					else:
						try:
							bot.remove_cog(module.capitalize())
							loadedmodule=importlib.reload(globals.modules[module])
							bot.add_cog(getattr(loadedmodule,module.capitalize())(bot))
						except AttributeError:
							importlib.reload(globals.modules[module])
							print('note: unable to reload '+module+' with discord.ext.commands support')
						except Exception as e: print(e)
						finally:
							await ctx.message.channel.send("reloaded `"+module+"` succesfully!")
				else:
					await ctx.message.channel.send('`'+module+"` isn't available for reloading.")
			else:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","reload")
	bot.add_cog(Reload(bot))
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
		if globals.modules['webserver']: asyncio.ensure_future(webserver.start())
		globals.connected=True
	
	with open(globals.store+"playing.txt","r") as file:
		playing=file.read().split()
	if len(playing)>1:
		print('changing status to '+' '.join(playing)+'...')
		mode=playing[0]
		status=' '.join(playing[1:])
		type={
			'playing':discord.ActivityType.playing,
			'streaming':discord.ActivityType.streaming,
			'watching':discord.ActivityType.watching,
			'listening':discord.ActivityType.listening
		}.get(mode,discord.ActivityType.unknown)
		
		await bot.change_presence(activity=discord.Activity(name=status,type=type))
	else:
		print('no playing status found')
		await bot.change_presence(activity=discord.Game(name='m/help'))
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
			await globals.meme.BackgroundService()
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
		asyncio.ensure_future(globals.janitor(message))
	# determine if message was posted in a meme channel, and if so determine if it is a meme
	if globals.modules['meme'] and message.channel.id in sum(globals.memechannels.values(),[]):
		asyncio.ensure_future(globals.meme.OnMemePosted(message))
	
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

async def send_ownerintro(server):
	em=discord.Embed(title="introducing merely",type='rich',inline=False,
	description="hello! i was just added to your server! type `merely help` for a list of general commands, but as the owner of *"+server.name+"*, you have more commands available to you;",
	color=discord.Colour(0x2C5ECA),url=globals.apiurl+'#/serverowner')
	em.add_field(name='merely welcome',value=help.dhelp['welcome'])
	em.add_field(name='merely farewell',value=help.dhelp['farewell'])
	em.add_field(name='merely janitor',value=help.dhelp['janitor'])
	em.add_field(name='merely clean',value=help.dhelp['clean'])
	em.add_field(name='merely purge',value=help.dhelp['purge'])
	em.add_field(name='merely die',value=help.dhelp['die'])
	em.add_field(name='merely blacklist and whitelist',value=help.dhelp['blacklist']+'\n\n'+help.dhelp['whitelist'])
	em.add_field(name='merely lockout',value=help.dhelp['lockout'])
	em.add_field(name='merely feedback',value="this command isn't exclusive, but be sure to use it!\n"+help.dhelp['feedback'])
	em.add_field(name='merely changelog',value="this command isn't exclusive, but be sure to use it!\n"+help.dhelp['changelog'])
	em.add_field(name='for more information...',value='be sure to visit merely\'s website! '+globals.apiurl+'#/serverowner')
	em.set_thumbnail(url=globals.emurl+"greet.gif")
	em.set_footer(text="merely v"+globals.ver+" - created by Yiays#5930", icon_url=globals.iconurl)
	await server.owner.send(embed=em)
	
@bot.event
async def on_guild_join(server):
	if globals.verbose: print(time.strftime("%H:%M:%S",time.localtime())+" - Joined server "+server.name+"!")
	if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - **Joined server *"+server.name+"*!** ["+str(server.id)+"]")
	
	await send_ownerintro(server)
	
	await bot.change_presence(activity=discord.Game(name='merely help | m/help'))
	await asyncio.sleep(30)
	# TODO: make universal playing function and use that
	# with open(globals.store+"playing.txt","r") as file:
		# playing=file.read()
	# if len(playing)>1:
		# await bot.change_presence(activity=discord.Game(name=playing))
	# else:
		# await bot.change_presence(activity=discord.Game(name='merely help'))

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
		await bot.get_channel(int(globals.config.get(str(member.guild.id),'welcome_channel'))).send(globals.config.get(str(member.guild.id),'welcome_message').format('<@'+str(member.id)+'>',member.guild.name))

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
	if msg.channel.id != globals.logchannel and (isinstance(msg.channel,discord.abc.PrivateChannel) or msg.author==bot.user or msg.author.id == globals.musicbuddy or bot.user in msg.mentions or msg.content.startswith('m/') or msg.content.startswith('merely')):
		if globals.modules['stats']:
			if msg.author==bot.user:
				globals.stats.sentcount+=1
			else:
				globals.stats.recievedcount+=1
		
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
	if e.channel_id in sum(globals.memechannels.values(),[]) and e.user_id != bot.user.id:
		await globals.meme.OnReaction(True,e.message_id,e.user_id,e.channel_id,e.emoji)
@bot.event
async def on_raw_reaction_remove(e):
	if e.channel_id in sum(globals.memechannels.values(),[]):
		await globals.meme.OnReaction(False,e.message_id,e.user_id)

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

if ('Merely' in os.environ and not globals.beta) or ('MerelyBeta' in os.environ and globals.beta):
	print('connecting...')
	bot.run(os.environ.get('Merely' if not globals.beta else 'MerelyBeta'))
else:
	print('ERROR: you must supply a token as an environment variable before merely can start.')

#shutdown

print('exited.')
