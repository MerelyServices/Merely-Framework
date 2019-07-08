"""
	Merely - created by Yiays#5930
	https://merely.yiays.com
	A Discord bot created to entertian, moderate, and inform.
"""

import os, sys, traceback, asyncio, time, importlib
import discord
from discord.ext import commands
import emformat, globals

#stdout to file
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
bot=commands.Bot(command_prefix=commands.when_mentioned_or('merely ','m/ ','m/'), help_attrs={'enabled':False},case_insensitive=True)
bot.remove_command('help')

globals.bot=bot

if globals.verbose: print('importing modules...')

# bot command modules
# globals
globals.modules['globals']=globals

# emformat
globals.modules['emformat']=emformat

#	help
import help
globals.modules['help']=help
bot.add_cog(help.Help(bot))
if globals.verbose: print('help done!')

#	censor
import censor
globals.modules['censor']=censor
bot.add_cog(censor.Censor(bot))
if globals.verbose: print('censor done!')

#	fun
import fun
globals.modules['fun']=fun
bot.add_cog(fun.Fun(bot))
if globals.verbose: print('fun done!')

#	meme
import meme
globals.memedbpass=os.environ.get("MemeDB")
globals.modules['meme']=meme
globals.meme = meme.Meme(bot)
bot.add_cog(globals.meme)
if globals.verbose: print('meme done!')

#	search
import search
globals.modules['search']=search
bot.add_cog(search.Search(bot))
if globals.verbose: print('search done!')

#	admin
import admin
globals.modules['admin']=admin
bot.add_cog(admin.Admin(bot))
if globals.verbose: print('admin done!')

#	obsolete
import obsolete
globals.modules['obsolete']=obsolete
bot.add_cog(obsolete.Obsolete(bot))
if globals.verbose: print('obsolete done!')

#	webserver
if globals.webserver:
	import webserver
	globals.modules['webserver']=webserver
if globals.verbose: print('webserver done!')

# stats
import stats
globals.modules['stats']=stats
globals.stats=stats.Stats()
bot.add_cog(globals.stats)
if globals.verbose: print('stats done!')

#	reload
globals.commandlist['reload']=['reload']

class Reload(commands.Cog):
	def __init__(self, bot):
		bot = bot
	@commands.command(pass_context=True,no_pm=False)
	async def reload(self,ctx,*,module:str):
		if ctx.message.author.id in globals.superusers:
			if module=='webserver':
				await globals.modules['webserver'].stop()
				webserver=importlib.reload(globals.modules[module])
				await webserver.start()
				await ctx.message.channel.send("reloaded `"+module+"` succesfully!")
			elif module=='stats':
				# globals.stats.stop()
				stats=importlib.reload(globals.modules[module])
				globals.stats=stats.Stats()
				await globals.stats.runstats()
				await ctx.message.channel.send("reloaded `"+module+"` succesfully!")
			elif module=='globals' or module=='config':
				globals.reload()
				await ctx.message.channel.send("reloaded `"+module+"` succesfully!")
			elif module in globals.modules and globals.modules[module]:
				try:
					bot.remove_cog(module.capitalize())
					loadedmodule=importlib.reload(globals.modules[module])
					bot.add_cog(getattr(loadedmodule,module.capitalize())(bot))
				except AttributeError:
					importlib.reload(globals.modules[module])
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
		if globals.webserver: asyncio.ensure_future(webserver.start())
		asyncio.ensure_future(globals.stats.runstats())
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
	
	if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - starting background service...")
	try:
		await globals.meme.BackgroundService()
	except Exception as e:
		if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - background service failed to complete!```"+str(e)+"```")
	else:
		if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - background service ended.")

@bot.event
async def on_message(message):
	await msglog(message)
	
	ctx = await bot.get_context(message)
	if ctx.prefix is not None:
		allowed=True
		if message.author.name+"#"+message.author.discriminator in globals.lockout:
			if int(globals.lockout[message.author.name+"#"+message.author.discriminator]) > time.time():
				allowed=False
				await message.channel.send("you've been banned from interacting with this bot. try again later, this may be temporary.")
				print('user '+message.author.name+"#"+message.author.discriminator+' is locked out for another '+str(int(globals.lockout[message.author.name+"#"+message.author.discriminator])-time.time())+' seconds.')
			else:
				await message.channel.send("your ban is over. you may use commands again.")
				globals.lockout.pop(message.author.name+"#"+message.author.discriminator,None)
				globals.save()
		if allowed:
			ctx.command = bot.get_command(ctx.invoked_with.lower())
			await bot.invoke(ctx)
	if message.channel.id in sum(globals.memechannels.values(),[]):
		await globals.meme.OnMemePosted(ctx.message)
	
	await janitor(message)

async def send_ownerintro(server):
	em=discord.Embed(title="introducing merely",type='rich',inline=False,
	description="hello! i was just added to your server *"+server.name+"*! type `merely help` for a list of general commands, but as the owner of *"+server.name+"*, you have more commands available to you;",
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
	em.add_field(name='for more information...',value='be sure to visit merely\s website! '+globals.apiurl+'#/serverowner')
	em.set_thumbnail(url=globals.emurl+"greet.gif")
	em.set_footer(text="merely v"+globals.ver+" - created by Yiays#5930", icon_url="https://cdn.discordapp.com/avatars/309270899909984267/1d574f78b4d4acec14c1ef8290a543cb.png?size=64")
	await server.owner.send(embed=em)
	
@bot.event
async def on_guild_join(server):
	if globals.verbose: print(time.strftime("%H:%M:%S",time.localtime())+" - Joined server "+server.name+"!")
	if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - **Joined server *"+server.name+"*!** ["+str(server.id)+"]")
	
	await send_ownerintro(server)
	
	await bot.change_presence(activity=discord.Game(name='merely help | m/help'))
	await asyncio.sleep(30)
	with open(globals.store+"playing.txt","r") as file:
		playing=file.read()
	if len(playing)>1:
		await bot.change_presence(activity=discord.Game(name=playing))
	else:
		await bot.change_presence(activity=discord.Game(name='merely help'))

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

async def msglog(msg):
	if globals.logchannel and msg.channel.id != globals.logchannel:
		if isinstance(msg.channel,discord.abc.PrivateChannel) or msg.author==bot.user or bot.user in msg.mentions or msg.content.startswith('m/') or msg.content.startswith('merely'):
			if msg.author==bot.user:
				globals.stats.sentcount+=1
			else:
				globals.stats.recievedcount+=1
			
			content=truncate(msg.content.encode('utf-8').decode('ascii','ignore'),64)
			fullcon=truncate(msg.content,64).replace('http','')
			
			if isinstance(msg.channel,discord.abc.PrivateChannel):
				channel='PM'
			else:
				channel=truncate(msg.guild.name,12)+'#'+truncate(msg.channel.name,12)
			
			print(time.strftime("%H:%M:%S",time.localtime())+" - ["+channel+"] "+msg.author.name+"#"+msg.author.discriminator+": "+content)
			if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - ["+channel+"] "+msg.author.name+"#"+msg.author.discriminator+": "+fullcon)

async def janitor(msg):
	globals.config.read(globals.store+'config.ini')
	if msg.channel.id in globals.config.get('janitor','strict').split(' '):
		await asyncio.sleep(30)
		try:
			await msg.delete()
		except Exception as e:
			print(e)
			return
	elif msg.channel.id in globals.config.get('janitor','relaxed').split(' '):
		if msg.author==bot.user or bot.user in msg.mentions or msg.content.lower().startswith('m/') or msg.content.lower().startswith('merely'):
			await asyncio.sleep(30)
			try:
				await msg.delete()
			except Exception as e:
				print(e)
				return

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
	if globals.logchannel:
		channel = bot.get_channel(globals.logchannel)
		await channel.send(time.strftime("%H:%M:%S",time.localtime())+" - **encountered an error;**\n```"+truncate(error,1950)+'```')
if globals.verbose: print('events done!')

print('connecting...')
bot.run(os.environ.get("Merely"))

#shutdown

print('exited.')
