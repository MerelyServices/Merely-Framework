"""
	Merely - created by Yiays#5930
	https://merely.yiays.com
	A Discord bot created to entertian, moderate, and inform.
	
	merelybot.py is a barebones core to be extended upon with plugins
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

if globals.verbose: print('setting up events...')
# Some events are not included for security purposes
bot.events={'on_connect':[],
						'on_disconnect':[],
						'on_ready':[],
						'on_shard_ready':[],
						'on_resumed':[],
						'on_error':[],
						'on_socket_raw_receive':[],
						'on_socket_raw_send':[],
						'on_typing':[],
						'on_message':[],
						'on_message_delete':[],
						'on_bulk_message_delete':[],
						'on_raw_message_delete':[],
						'on_raw_bulk_message_delete':[],
						'on_message_edit':[],
						'on_raw_message_edit':[],
						'on_reaction_add':[],
						'on_raw_reaction_add':[],
						'on_reaction_remove':[],
						'on_raw_reaction_remove':[],
						'on_reaction_clear':[],
						'on_raw_reaction_clear':[],
						'on_reaction_clear_emoji':[],
						'on_raw_reaction_clear_emoji':[],
						'on_private_channel_delete':[],
						'on_private_channel_create':[],
						'on_private_channel_update':[],
						'on_private_channel_pins_update':[],
						'on_guild_channel_delete':[],
						'on_guild_channel_create':[],
						'on_guild_channel_update':[],
						'on_guild_channel_pins_update':[],
						'on_guild_integrations_update':[],
						'on_webhooks_update':[],
						'on_member_join':[],
						'on_member_remove':[],
						'on_member_update':[],
						'on_user_update':[],
						'on_guild_join':[],
						'on_guild_remove':[],
						'on_guild_update':[],
						'on_guild_role_create':[],
						'on_guild_role_delete':[],
						'on_guild_role_update':[],
						'on_guild_emojis_update':[],
						'on_guild_available':[],
						'on_guild_unavailable':[],
						'on_voice_state_update':[],
						'on_member_ban':[],
						'on_member_unban':[],
						'on_invite_create':[],
						'on_invite_delete':[]
						}

@bot.event
async def on_connect():
	for func in bot.events['on_connect']:
		asyncio.ensure_future(func())

@bot.event
async def on_disconnect():
	for func in bot.events['on_disconnect']:
		asyncio.ensure_future(func())

@bot.event
async def on_ready():
	for func in bot.events['on_ready']:
		asyncio.ensure_future(func())

@bot.event
async def on_shard_ready(shard_id):
	for func in bot.events['on_shard_ready']:
		asyncio.ensure_future(func(shard_id))

@bot.event
async def on_resumed():
	for func in bot.events['on_resumed']:
		asyncio.ensure_future(func())

@bot.event
async def on_error(event, *args, **kwargs):
	raise #TODO: get this working
	#for func in bot.events['on_error']:
		#asyncio.ensure_future(func(event, *args, **kwargs))

@bot.event
async def on_socket_raw_receive(msg):
	for func in bot.events['on_socket_raw_receive']:
		asyncio.ensure_future(func(msg))

@bot.event
async def on_socket_raw_send(payload):
	for func in bot.events['on_socket_raw_send']:
		asyncio.ensure_future(func(payload))

@bot.event
async def on_typing(channel, user, when):
	for func in bot.events['on_typing']:
		asyncio.ensure_future(func(channel, user, when))

@bot.event
async def on_message(message):
	for func in bot.events['on_message']:
		asyncio.ensure_future(func(message))

@bot.event
async def on_message_delete(message):
	for func in bot.events['on_message_delete']:
		asyncio.ensure_future(func(message))

@bot.event
async def on_bulk_message_delete(messages):
	for func in bot.events['on_bulk_message_delete']:
		asyncio.ensure_future(func(messages))

@bot.event
async def on_raw_message_delete(payload):
	for func in bot.events['on_raw_message_delete']:
		asyncio.ensure_future(func(payload))

@bot.event
async def on_raw_bulk_message_delete(payload):
	for func in bot.events['on_raw_bulk_message_delete']:
		asyncio.ensure_future(func(payload))

@bot.event
async def on_message_edit(before, after):
	for func in bot.events['on_message_edit']:
		asyncio.ensure_future(func(before, after))

@bot.event
async def on_raw_message_edit(payload):
	for func in bot.events['on_raw_message_edit']:
		asyncio.ensure_future(func(payload))

@bot.event
async def on_reaction_add(reaction, user):
	for func in bot.events['on_reaction_add']:
		asyncio.ensure_future(func(reaction, user))

@bot.event
async def on_raw_reaction_add(payload):
	for func in bot.events['on_raw_reaction_add']:
		asyncio.ensure_future(func(payload))

@bot.event
async def on_reaction_remove(reaction, user):
	for func in bot.events['on_reaction_remove']:
		asyncio.ensure_future(func(reaction, user))

@bot.event
async def on_raw_reaction_remove(payload):
	for func in bot.events['on_raw_reaction_remove']:
		asyncio.ensure_future(func(payload))

@bot.event
async def on_reaction_clear(message, reactions):
	for func in bot.events['on_reaction_clear']:
		asyncio.ensure_future(func(message, reactions))

@bot.event
async def on_raw_reaction_clear(payload):
	for func in bot.events['on_raw_reaction_clear']:
		asyncio.ensure_future(func(payload))

@bot.event
async def on_reaction_clear_emoji(reaction):
	for func in bot.events['on_reaction_clear_emoji']:
		asyncio.ensure_future(func(reaction))

@bot.event
async def on_raw_reaction_clear_emoji(payload):
	for func in bot.events['on_raw_reaction_clear_emoji']:
		asyncio.ensure_future(func(payload))

@bot.event
async def on_private_channel_delete(channel):
	for func in bot.events['on_private_channel_delete']:
		asyncio.ensure_future(func(channel))

@bot.event
async def on_private_channel_create(channel):
	for func in bot.events['on_private_channel_create']:
		asyncio.ensure_future(func(channel))

@bot.event
async def on_private_channel_update(before, after):
	for func in bot.events['on_private_channel_update']:
		asyncio.ensure_future(func(before, after))

@bot.event
async def on_private_channel_pins_update(channel, last_pin):
	for func in bot.events['on_private_channel_pins_update']:
		asyncio.ensure_future(func(channel, last_pin))

@bot.event
async def on_guild_channel_delete(channel):
	for func in bot.events['on_guild_channel_delete']:
		asyncio.ensure_future(func(channel))

@bot.event
async def on_guild_channel_create(channel):
	for func in bot.events['on_guild_channel_create']:
		asyncio.ensure_future(func(channel))

@bot.event
async def on_guild_channel_update(before, after):
	for func in bot.events['on_guild_channel_update']:
		asyncio.ensure_future(func(before, after))

@bot.event
async def on_guild_channel_pins_update(channel, last_pin):
	for func in bot.events['on_guild_channel_pins_update']:
		asyncio.ensure_future(func(channel, last_pin))

@bot.event
async def on_guild_integrations_update(guild):
	for func in bot.events['on_guild_integrations_update']:
		asyncio.ensure_future(func(guild))

@bot.event
async def on_webhooks_update(channel):
	for func in bot.events['on_webhooks_update']:
		asyncio.ensure_future(func(channel))

@bot.event
async def on_member_join(member):
	for func in bot.events['on_member_join']:
		asyncio.ensure_future(func(member))

@bot.event
async def on_member_remove(member):
	for func in bot.events['on_member_remove']:
		asyncio.ensure_future(func(member))

@bot.event
async def on_member_update(before, after):
	for func in bot.events['on_member_update']:
		asyncio.ensure_future(func(before, after))

@bot.event
async def on_user_update(before, after):
	for func in bot.events['on_user_update']:
		asyncio.ensure_future(func(before, after))

@bot.event
async def on_guild_join(guild):
	for func in bot.events['on_guild_join']:
		asyncio.ensure_future(func(guild))

@bot.event
async def on_guild_remove(guild):
	for func in bot.events['on_guild_remove']:
		asyncio.ensure_future(func(guild))

@bot.event
async def on_guild_update(before, after):
	for func in bot.events['on_guild_update']:
		asyncio.ensure_future(func(before, after))

@bot.event
async def on_guild_role_create(role):
	for func in bot.events['on_guild_role_create']:
		asyncio.ensure_future(func(role))

@bot.event
async def on_guild_role_delete(role):
	for func in bot.events['on_guild_role_delete']:
		asyncio.ensure_future(func(role))

@bot.event
async def on_guild_role_update(before, after):
	for func in bot.events['on_guild_role_update']:
		asyncio.ensure_future(func(before, after))

@bot.event
async def on_guild_emojis_update(guild, before, after):
	for func in bot.events['on_guild_emojis_update']:
		asyncio.ensure_future(func(guild, before, after))

@bot.event
async def on_guild_available(guild):
	for func in bot.events['on_guild_available']:
		asyncio.ensure_future(func(guild))

@bot.event
async def on_guild_unavailable(guild):
	for func in bot.events['on_guild_unavailable']:
		asyncio.ensure_future(func(guild))

@bot.event
async def on_voice_state_update(member, before, after):
	for func in bot.events['on_voice_state_update']:
		asyncio.ensure_future(func(member, before, after))

@bot.event
async def on_member_ban(guild, user):
	for func in bot.events['on_member_ban']:
		asyncio.ensure_future(func(guild, user))

@bot.event
async def on_member_unban(guild, user):
	for func in bot.events['on_member_unban']:
		asyncio.ensure_future(func(guild, user))

@bot.event
async def on_invite_create(invite):
	for func in bot.events['on_invite_create']:
		asyncio.ensure_future(func(invite))

@bot.event
async def on_invite_delete(invite):
	for func in bot.events['on_invite_delete']:
		asyncio.ensure_future(func(invite))

if globals.verbose: print('events done!')

if globals.verbose: print('importing modules...')

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
		
		@commands.command(pass_context=True,no_pm=False)
		async def load(self,ctx,*,modulename:str):
			modulename = modulename.lower()
			if ctx.message.author.id in globals.superusers:
				# if module exists
				if modulename in globals.modules:
					try:
						# - load the module
						loadedmodule = importlib.import_module(modulename)
						
						# modules that need extra parameters
						if modulename in ['meme', 'tools']:
							bot.add_cog(getattr(loadedmodule, modulename.capitalize())(bot, os.environ.get("MemeDB")))
						# start the module the normal way
						else:
							bot.add_cog(getattr(loadedmodule, modulename.capitalize())(bot))
						
						# start other components of the module
						if modulename=='webserver':
							asyncio.ensure_future(bot.cogs['Webserver'].start())
					
					except Exception as e:
						print(e)
						await ctx.message.channel.send("failed to load `"+modulename+"`!")
						return
					
					globals.modules[modulename] = True
					await ctx.message.channel.send("loaded `"+modulename+"` succesfully!")
				else:
					await ctx.message.channel.send('`'+modulename+"` isn't available for loading.")
			else:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","load")
		
		@commands.command(pass_context=True,no_pm=False)
		async def unload(self,ctx,*,modulename:str):
			modulename = modulename.lower()
			if ctx.message.author.id in globals.superusers:
				# if module exists and is currently in cogs
				if modulename in globals.modules and modulename.capitalize() in bot.cogs:
					# edge case module that needs special treatment
					if modulename in ['config', 'core', 'emformat']:
						await ctx.message.channel.send('`'+modulename+"` must remain loaded for stability!")
						return
					
					cog = bot.cogs[modulename.capitalize()]
					
					# modules that need to be cleaned up before shutting down
					if modulename=='webserver':
						await cog.stop()
					
					# dereferencing the module and letting gc take care of it
					bot.remove_cog(modulename.capitalize())
					
					del sys.modules[modulename]
					
					globals.modules[modulename] = False
					await ctx.message.channel.send("unloaded `"+modulename+"` succesfully!")
				else:
					await ctx.message.channel.send('`'+modulename+"` isn't available for unloading!")
			else:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","load")
	
	bot.add_cog(Core(bot))
	if globals.verbose: print('reload done!')

async def onconnect():
	print('connected!')
bot.events['on_connect'].append(onconnect)

async def onready():
	print('logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	
	if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - **logged in and restored settings.**")
bot.events['on_ready'].append(onready)

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
bot.events['on_message'].append(command_handler)

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
	
async def log_guildjoin(server):
	if globals.verbose: print(time.strftime("%H:%M:%S",time.localtime())+" - Joined server "+server.name+"!")
	if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - **Joined server *"+server.name+"*!** ["+str(server.id)+"]")
	
	await bot.change_presence(activity=discord.Game(name=f"{globals.prefix_long} help | {globals.prefix_short}help"))
	if globals.modules['fun']:
		await asyncio.sleep(30)
		await bot.cogs['Fun'].recover_status()
bot.events['on_guild_join'].append(log_guildjoin)

async def log_guildleave(server):
	if globals.verbose: print(time.strftime("%H:%M:%S",time.localtime())+" - Left server "+server.name+"!")
	if globals.logchannel: await bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - **Left server *"+server.name+"*!**")
bot.events['on_guild_remove'].append(log_guildleave)

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
bot.events['on_message'].append(msglog)

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
bot.events['on_error'].append(log_error)

if __name__ == '__main__':
	if ('Merely' in os.environ and not globals.beta) or ('MerelyBeta' in os.environ and globals.beta):
		print('connecting...')
		bot.run(os.environ.get('Merely' if not globals.beta else 'MerelyBeta'))
	else:
		print('ERROR: you must supply a token as an environment variable before merely can start.')

	#shutdown

	print('exited.')
