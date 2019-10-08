import globals, emformat
from discord.ext import commands
import time, random, asyncio

globals.commandlist['help']=['help','command','hint','info','stats','about','feedback']

helpdict={
	':grey_question: help':'```help, command, hint, feedback```',
	':information_source:':'```info, stats, servers, changelog```',
	':mag_right: search':'```command, google, image```',
	':joy: fun':'```playing, meme, echo, thonk, vote```',
	':see_no_evil: censor':'```blacklist, whitelist, clean, purge```',
	':new: new':'```changelog, vote, dice```'
}
dhelp={
	'welcome':"***merely welcome [get|clear|set (welcome message)]***\n**SERVER OWNERS ONLY** - get the welcome message for the server or set it, use `merely welcome get` for instructions on how to set a welcome message.",
	'farewell':"***merely farewell [get|clear|set (farewell message)]***\n**SERVER OWNERS ONLY** - get the farewell message for the server or set it, use `merely farewell get` for instructions on how to set a farewell message.",
	'janitor':"***merely janitor [leave|join (strict|relaxed)]***\n**SERVER OWNERS ONLY** - opt into or opt out of the janitor service, the janitor deletes all messages after 30 seconds. in relaxed mode, janitor only deletes messages to and from merely.",
	'feedback':"***merely feedback (feedback)***\nthis forwards the feedback to the developer so that they can further improve the bot.",
	'help':"***merely help [(command)]***\nhelp offers a list of commands, if you follow merely help with a bot and a command, it'll describe the command in detail.",
	'info':"***merely info***\nfind out exactly what merely can do and get relevant links.",
	'stats':"***merely stats***\ntechnical information and interesting statistics.",
	'clean':"***merely clean [limit] [strict]***\nclean deletes all messages that either activated merely or are from merely in the current channel. If you provide a limit and the word 'strict' at the end, it will delete everything indescriminately.\n\n*note that all discord bots are only allowed to delete messages from the last 2 months.*",
	'purge':"***merely purge first-id last-id [limit]***\npurge purges all messages that are within a range of ids. get message ids by enabling developer mode in discord and then clicking on the menu next to the messages.",
	'playing':"***merely playing|watching|streaming [(status)]***\nchanges the playing status text to anything you desire, or alternatively resets the playing text if you provide no arguments.",
	'command':"***merely command (search)***\nsearches the list of known commands for any command containing the query.",
	'image':"***merely image more|(search)***\nsearches google images for your query and returns the top image. more returns 5 results.",
	'google':"***merely google more|(search)***\nsearches google for your query and returns the top search result. more returns the top 5 results.",
	'meme':"***merely meme [n | #(number)]***\nsends a random meme to the channel. n specifies how many you want, #(number) specifies the id of a meme you've seen before.\n\n*merely meme is designed to avoid repeating memes for as long as possible*",
	'thonk':"***merely thonk***\nit just posts a thonking emoji.",
	'vote':"***merely vote question? answer 1, answer 2, as many more answers as you want** - spaces, question marks and commas are important!*\nhold a vote with the given options, if you add a number at the end, that will be the time limit in minutes before the results are finalised. it might be possible for a vote to last forever in the near future...",
	'blacklist':"***merely blacklist [add|remove (word|url)]***\nblacklist lists all banned words. you can also add or remove one word at a time to the blacklist\n\n*note that the blacklist exists to prevent users from searching for nsfw content on non-nsfw channels in line with discord's terms of service.*",
	'whitelist':"***merely whitelist [add|remove (word|url)]***\nwhitelist lists all words that are exempt to the blacklist. you can also add or remove one word at a time to the whitelist.\n\n*note that the whitelist exists because the blacklist may mistake valid words as mispellings of bad words. as a server owner, you are allowed to fix this.*",
	'hint':"***merely hint***\ngives you handy hints on how to better use this bot.",
	'echo':"***merely echo (echo)***\nrepeats whatever you say to it. and no, it will not echo itself or other bots.",
	'dice':"***merely dice [(dice1sides) (dice2sides) (dice3sides) (dice4sides) (dice5sides) etc...]***\ndice will roll a 6 sided dice by default, but you can specify how many sides if you want, just leave a number, if you want to roll more than one dice, just leave more than one number.",
	'lockout':"***merely lockout (user#discriminator) [time in minutes]***\nprevents any user from interacting with the bot if it appears they are trying to abuse it.",
	'servers':"***merely servers***\nlists all the servers merely is in with an interactive page list system. also shows how many members each server has.",
	'logcat':"***merely logcat***\noutputs the last 10 lines in the log, for the sake of debugging.",
	'reload':"***merely reload (module)***\nthis command reloads changes made to merely's code without restarting the bot. available only to Yiays.",
	'changelog':"***merely changelog***\nlists all the recent changes made to merely over the previous few updates.",
	'die':"***merely die***\nshuts down merely if you have permission to do so. merely will restart in 30 seconds. this fixes issues with the bot being unresponsive."
}
globals.dhelp=dhelp

class Help(commands.Cog):
	"""Help related commands."""
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True, no_pm=False, aliases=['?','??'])
	async def help(self, ctx, *, search=None):
		"""Lists available commands"""
		if globals.verbose: print('help command')
		if search == None:
			await emformat.make_embed(ctx.message.channel,'go to '+globals.apiurl+' to learn more!',
				"merely help",":grey_question: for specific help, use `merely help [command]`\n:mag_right: to search for commands, use `merely command [search]`"+\
				"\n:bulb: for hints, use `merely hint`\n:point_up_2: click *'merely help'* above to go to the official website with even more information!*\n",
				0x2C5ECA,'',globals.apiurl+"#/help",helpdict,
				"merely v"+globals.ver+" - created by Yiays#5930",
				"https://cdn.discordapp.com/avatars/309270899909984267/1d574f78b4d4acec14c1ef8290a543cb.png?size=64",
				globals.apiurl+'#/help'
			)
			if random.random() < 1/3:
				await ctx.message.channel.send('consider upvoting merely on the discord bot list; https://discordbots.org/bot/309270899909984267')
		else: #detailed help
			if search in dhelp: await emformat.genericmsg(ctx.message.channel,dhelp[search],"help","help")
			else: await emformat.genericmsg(ctx.message.channel,"either the command, `"+search+"`, doesn't exist, or it doesn't have any documentation yet.","error","help")

	@commands.command(pass_context=True, no_pm=False, aliases=['commands'])
	async def command(self, ctx, *, search=None):
		"""Searching existing commands"""
		if globals.verbose: print('command command')
		if search==None: await emformat.genericmsg(ctx.message.channel,dhelp['command'],"help","command")
		else:
			matches=[s for s in dhelp if search in s or search in dhelp[s]]
			if matches:
				matchstr=""
				for match in matches:
					matchstr+=dhelp[match]+"\n"
				await emformat.genericmsg(ctx.message.channel,"here's all matches;\n"+matchstr,"help","command")
			else:
				await emformat.genericmsg(ctx.message.channel,"i couldn't find a command matching that search term.","error",'command')

	@commands.command(pass_context=True, no_pm=False)
	async def hint(self,ctx):
		"""Give users hints on how to use merely"""
		if globals.verbose: print('hint command')
		await emformat.make_embed(ctx.message.channel,'',title="Did you know...",
				description=random.choice(
				["`merely help` followed by a command name explains the command in more detail...",
				 "click the title of any command's message to be taken to the online docs.",
				 "`merely clean [n]` scans the last [n] messages for messages to and from merely and deletes matches.",
				 "`merely clean [n] strict` deletes all of the last [n] messages. only admins can use this.",
				 "search for commands with `merely command <search>`!",
				 "tired of typing `merely`? `m/` also works as a prefix, as does `@merely`. use whichever is easiest.",
				 "`merely info` shows off the features of merely and gives you a few relevant links.",
				 "`merely stats` shows technical information about what the bot runs on and how much work it's doing.",
				 "set the playing status of merely with `merely playing <status>.`",
				 #"`m/blacklist`, `m/whitelist` and `m/meme` have a public list and a private list, changes made on your server effect only your server.",
				 "`m/thonk` is objectively the most valuable command on this bot. it makes use of Discord Nitro to bring you the best emoji.",
				 "`m/vote` is one of the most advanced commands made yet! it supports live updating polls, countdown timers and helps decide a winner.",
				 "`m/vote supports holding a vote for up to 4 hours, though the longer a poll is running the more likely that it may fail.`",
				 "like merely? consider upvoting merely on the discord bot list; https://discordbots.org/bot/309270899909984267",
				 "*no hints for you lol*"]),
				color=0xf4e242,
				author='Handy Hints with merely',
				footer="merely v"+globals.ver+" - created by Yiays#5930"
			)
	
	@commands.command(pass_context=True, no_pm=False, aliases=['about'])
	async def info(self,ctx):
		if globals.verbose:print('info command')
		
		m, s = divmod(time.time()-globals.stats.starttime, 60)
		h, m = divmod(m, 60)
		
		await emformat.make_embed(ctx.message.channel,'go to '+globals.apiurl+' to learn more!','merely info','',0x2C5ECA,'',globals.emurl+'greet.gif',
		{
		'🆕 fantastic features!':"merely can do lots of stuff, it currently has **"+str(len(dhelp))+"** commands available to **"+str(len(self.bot.guilds))+"** servers.\ntype `merely help` for a full list of commands or type `merely changelog` to see all the recent additions and fixes!",
		'😊🤖 mobile and human friendly!':"merely is activated by 3 prefixes; `merely <command>`, `m/<command>` and `@merely <command>` pick whichever is easiest for you to type on your device.",
		'📚 detailed documentation!':"if you're unsure what a command does; `merely help <command>`. if you can't find a command; `merely commands <search>`. if you want to learn something new; `merely hint`. if you still need help, you can click the title of the embed for online documentation (<:soon:233642257817927680>)!",
		'⬆️ frequent updates!':'merely is updated with more features automatically all the time, almost seamlessly. thanks to sharding (coming soon) and modular design, merely can stay online 24/7 even when being updated!\n merely has been online constantly for '+str(round(h))+" hours, "+str(round(m))+" minutes and "+str(round(s))+" seconds.",
		#'👥 sharding! <:soon:233642257817927680>':"merely will provide optimal service to all users in the future by being hosted on multiple servers around the world! the fastest and slowest bots will dynamically connect to your server based on demand!",
		'➕ add now!':"[click here](https://discordapp.com/oauth2/authorize?client_id=309270899909984267&scope=bot&permissions=104131650) to add merely to your server with minimal permissions. *note that merely may have to ask for more permissions later on.*",
		'💡 keep the lights on':"consider voting for this bot at [discordbots.org](https://discordbots.org/bot/309270899909984267) if you enjoy it's services! the developers would really appreciate it!"
		},
		'','',globals.apiurl)
	
	@commands.command(pass_context=True, no_pm=False)
	async def feedback(self,ctx,*,feedback):
		if globals.verbose:print('feedback command')
		owner=self.bot.get_user(globals.owner)
		if globals.feedbackchannel:
			try:
				await self.bot.get_channel(globals.feedbackchannel).send("<@!140297042709708800>, feedback from @{}#{} in {};```{}```".format(ctx.message.author.name,ctx.message.author.discriminator,ctx.message.guild.name,feedback))
			except Exception as e:
				print(e)
				await self.bot.get_channel(globals.feedbackchannel).send("<@!140297042709708800>, feedback from @{}#{};```{}```".format(ctx.message.author.name,ctx.message.author.discriminator,feedback))
			await emformat.genericmsg(ctx.message.channel,"feedback sent!","done","feedback")
			if owner is None or globals.invite is None:
				await ctx.message.author.send("thanks for your feedback.\nthe owner of this bot hasn't provided contact details, however they may send a friend request if they require further information.")
			else:
				await ctx.message.author.send("thanks for your feedback.\nyou may receive a friend request from "+owner.username+'#'+owner.discriminator+" if further information is needed.\n"+\
																			"alternatively, join merely's main discord server, and we can talk directly there; https://discord.gg/"+globals.invite)
			await ctx.message.channel.send("feedback sent!")
		else:
			await ctx.message.channel.send("unfortunately, the administrator of merely currently doesn't have a channel in place for receiving feedback. the developers should find your feedback in the logs.")
	@feedback.error
	async def feedback_error(self,ctx,error):
		print(error)
		await emformat.genericmsg(ctx.message.channel,"unfortunately there was an error when trying to send your feedback, but the developers will read this error and find your feedback here.","error","feedback")
	