import globals, emformat, utils
from discord.ext import commands
import time, random, asyncio

# ['help']=['help','command','hint','info','stats','feedback']

helpdict={
	':grey_question: help':'```help, command, hint, feedback```',
	':information_source:':'```info, stats, servers, changelog```',
	':joy: fun':'```playing, meme, echo, thonk, vote, dice```',
	':tools: tools':'```shorten```',
	':levitate: admin':'```blacklist, whitelist, clean, purge```',
	':new: new':'```changelog, dice, shorten```'
}
dhelp={
	'welcome':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}welcome [get|clear|set (welcome message)]***\n**SERVER OWNERS ONLY** - get the welcome message for the server or set it, use `{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}welcome set` for instructions on how to set a welcome message.",
	'farewell':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}farewell [get|clear|set (farewell message)]***\n**SERVER OWNERS ONLY** - get the farewell message for the server or set it, use `{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}farewell set` for instructions on how to set a farewell message.",
	'janitor':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}janitor [leave|join (strict|relaxed)]***\n**SERVER OWNERS ONLY** - opt into or opt out of the janitor service, the janitor deletes all messages after 30 seconds. in relaxed mode, janitor only deletes messages to and from merely.",
	'feedback':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}feedback (feedback)***\nthis forwards the feedback to the developer so that they can further improve the bot.",
	'help':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}help [(command)]***\nhelp offers a list of commands, if you follow {globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}help with a bot and a command, it'll describe the command in detail.",
	'info':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}info***\nfind out exactly what {globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}can do and get relevant links.",
	'stats':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}stats***\ntechnical information and interesting statistics.",
	'clean':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}clean [limit] [strict]***\n**MODERATORS ONLY** - clean deletes all messages that either activated {globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}or are from {globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}in the current channel. If you provide a limit and the word 'strict' at the end, it will delete everything indescriminately.\n\n*note that all discord bots are only allowed to delete messages from the last 2 months.*",
	'purge':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}purge (first message id) (last message id) [limit]***\n**MODS ONLY** - purge purges all messages that are within a range of ids. get message ids by enabling developer mode in discord and then clicking on the menu next to the messages.",
	'playing':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}playing|watching|streaming [(status)]***\nchanges the playing status text to anything you desire, or alternatively resets the playing text if you provide no arguments. is subject to censorship from the blacklist.",
	'command':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}command (search)***\nsearches the list of known commands for any command containing the query.",
	'image':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}image more|(search)***\nsearches google images for your query and returns the top image. `{globals.prefix_short}image more` returns 5 more results, `{globals.prefix_short}images` returns 5 from the begining.",
	'google':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}google more|(search)***\nsearches google for your query and returns the top search result. more returns the top 5 results.",
	'meme':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}meme [n | #(number)]***\nsends a random meme to the channel. n specifies how many you want, #(number) specifies the id of a meme you've seen before.\n\n*{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}meme is designed to avoid repeating memes for as long as possible*",
	'thonk':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}thonk***\nit just posts a random thonking emoji.",
	'vote':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}vote question? answer 1, answer 2, as many more answers as you want** - spaces, question marks and commas are important!*\ncreate an interactive, multi-choice poll with the given options, if you add a number at the end, that will be the time limit in minutes before the results are finalised. the longer a poll is running, the more likely it may fail to complete.",
	'blacklist':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}blacklist [add (words)|remove (words)|train (url)]***\n**SERVER OWNERS ONLY** - blacklist lists all banned words. you can also add or remove one word at a time to your server's local blacklist\n\n*note that the blacklist exists to prevent users from searching for nsfw content on non-nsfw channels in line with discord's terms of service.*",
	'whitelist':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}whitelist [add (words)|remove (words)|train (url)]***\n**SERVER OWNERS ONLY** - whitelist lists all words that are exempt to the blacklist. you can also add or remove one word at a time to your server's local whitelist.\n\n*note that the whitelist exists because the blacklist may mistake valid words as mispellings of bad words. as a server owner, you are allowed to fix this.*",
	'hint':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}hint***\ngives you handy hints on how to better use this bot.",
	'echo':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}echo (echo)***\nrepeats whatever you say to it. and no, it will not echo itself or other bots. is subject to censorship rules in the blacklist.",
	'dice':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}dice [(dice1sides) (dice2sides) (dice3sides) (dice4sides) (dice5sides) etc...]***\ndice will roll a 6 sided dice by default, but you can specify how many sides if you want, just leave a number, if you want to roll more than one dice, just leave more than one number separated by spaces.",
	'lockout':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}lockout (user#discriminator) [time in minutes]***\n**SERVER OWNERS ONLY** - prevents any user from interacting with the bot if it appears they are trying to abuse it.",
	'servers':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}servers***\nlists all the servers {globals.name} is in with an interactive page list system. also shows how many members each server has.",
	'logcat':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}logcat (lines)***\noutputs the last 10 lines, by default, in the log, for the sake of debugging.",
	'reload':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}reload (module)***\n**MERELY SUPERUSERS ONLY** - this command reloads changes made to merely's code without restarting the bot.",
	'changelog':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}changelog***\nlists all the recent changes made to {globals.name} over the previous few updates.",
	'shorten':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}shorten (long link) [short name]***\ntakes the provided long link and shortens it using https://l.yiays.com. If the requested short link is *0*, the short link will be randomized.",
	'die':f"***{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}die***\n**MERELY SUPERUSERS ONLY** - shuts down {globals.name} safely."
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
				"\n:bulb: for hints, use `merely hint`\n:point_up_2: click *'merely help'* above to go to the official website with even more information!\n",
				color=0x2C5ECA,thumbnail=globals.emurl+"help.gif",fields=helpdict,
				footer="merely v"+globals.ver+" - created by Yiays#5930",
				icon=globals.iconurl,
				link=globals.apiurl+'#/help'
			)
			#if random.random() < 1/3:
				#await ctx.message.channel.send('consider upvoting merely on the discord bot list; https://discordbots.org/bot/309270899909984267')
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
				[f"`merely help` followed by a command name explains the command in more detail. eg. `{globals.prefix_short}help meme`",
				 "click the title of any command's message to be taken to the online docs, which includes interactive tutorials for each command!",
				 "`merely clean [n]` scans the last [n] messages for messages to and from merely and deletes matches. only mods can use this.",
				 "`merely clean [n] strict` deletes all of the last [n] messages. only admins can use this.",
				 "search for commands with `merely command <search>` - it'll try its best to match you with the command you're looking for!",
				 f"tired of typing `{globals.prefix_long}`? `{globals.prefix_short}` also works as a prefix, as does `@{globals.name}`. use whichever is easiest.",
				 "`merely info` shows off the features of merely and gives you a few relevant links.",
				 "`merely stats` shows technical information about what the bot runs on and how much work it's doing.",
				 "set the playing status of merely with `merely (playing|watching|streaming|listening) (status)`",
				 f"`{globals.prefix_short}blacklist`, `{globals.prefix_short}whitelist` and `{globals.prefix_short}meme` have a public list and a private list, changes made on your server affect only your server.",
				 f"`{globals.prefix_short}thonk` is the best command. it makes use of Discord Nitro to bring you 50+ thinking emoji.",
				 f"`{globals.prefix_short}vote` is one of the most advanced commands made yet! it supports live updating polls, countdown timers and helps decide a winner."#,
				 #"like merely? consider upvoting merely on the discord bot list; https://discordbots.org/bot/309270899909984267"
				]),
				color=0xf4e242,
				author='Handy Hints with merely',
				icon=globals.iconurl,
				footer="merely v"+globals.ver+" - created by Yiays#5930"
			)
	
	@commands.command(pass_context=True, no_pm=False, aliases=['about'])
	async def info(self,ctx):
		if globals.verbose:print('info command')
		
		await emformat.make_embed(ctx.message.channel,'go to '+globals.apiurl+' to learn more!','merely info','',color=0x2C5ECA,thumbnail=globals.emurl+'greet.gif',
		fields={
		'🆕 fantastic features!':f"{globals.name} can do lots of stuff, it currently has **{len(dhelp)}** commands available to **{len(self.bot.guilds)}** servers.\ntype `{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}help` for a full list of commands or type `{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}changelog` to see all the recent additions and fixes!",
		'😊🤖 mobile and human friendly!':f"{globals.name} is activated by 3 prefixes; `{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}<command>`, `{globals.prefix_short}<command>` and `@{globals.name} <command>` pick whichever is easiest for you to type on your device.",
		'📚 detailed documentation!':f"if you're unsure what a command does; `{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}help <command>`. if you can't find a command; `{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}commands <search>`. if you want to learn something new; `{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}hint`. if you still need help, you can click the title of the embed for online documentation!",
		'⬆️ frequent updates!':f"{globals.name} is updated with more features automatically, without interruption, thanks to a modular design, {globals.name} can stay online 24/7 even when being updated!\n{globals.name} has been online constantly for {utils.time_fold(time.time()-self.bot.cogs['Stats'].starttime)}",
		#'👥 sharding! <:soon:233642257817927680>':f"merely will provide optimal service to all users in the future by being hosted on multiple servers around the world! the fastest and slowest bots will dynamically connect to your server based on demand!",
		'➕ add now!':f"[click here](https://discordapp.com/oauth2/authorize?client_id={self.bot.id}&scope=bot&permissions=104131650) to add {globals.name} to your server with minimal permissions. *note that {globals.name} may need to ask for more permissions later on.*"#,
		#'💡 keep the lights on':f"consider voting for this bot at [discordbots.org](https://discordbots.org/bot/309270899909984267) if you enjoy its services! the developers would really appreciate it!"
		},
		link=globals.apiurl,
		icon=globals.iconurl,
		footer=f"{globals.name} v{globals.ver} - created by Yiays#5930")
	
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
		await emformat.genericmsg(ctx.message.channel,"unfortunately there was an error when trying to send your feedback, but the developers should read this error and find your feedback.","error","feedback")
	