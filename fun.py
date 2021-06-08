import globals
import asyncio
import random
import discord
import math, re, time
from discord.ext import commands
import emformat, utils
import help

# ['fun']=['playing','thonk','vote','dice','echo']

class Fun(commands.Cog):
	"""Fun related commands."""
	def __init__(self, bot):
		self.bot = bot
		self.lastmeme={}
		self.usedmemes=[]
		self.thonks=globals.thonks.split(' ')
		
	def printvote(self,q,v,t,e):
		if t-time.time()>=1:
			min,sec=divmod(round(t-time.time()),60)
			countdown='{}:{:02d}'.format(min,sec)
		else:
			countdown="time's up!"
		
		str=f'**{q}**\n\n⏰ {countdown}\n\n'
		mostvotes=max(v.values())
		i=0
		for option,votes in v.items():
			if mostvotes==0: vp = 0
			else: vp=votes/mostvotes
			str+=f'{e[i]}`[{"■"*round(vp*10)+"□"*round(10-vp*10)}] {votes}` - {option}\n'
			i+=1
		str+='\n\nuse the reactions below to add your vote!'
		
		em=discord.Embed(type='rich', description=str, url=globals.apiurl+'#/vote')
		
		return em

	@commands.command(pass_context=True, no_pm=False, aliases=['watching','streaming','listening'])
	async def playing(self, ctx, *, status=''):
		"""Controls the bot status"""
		
		if ctx.message.author.id in globals.authusers:
			mode=ctx.invoked_with.lower()
			type={
				'playing':discord.ActivityType.playing,
				'streaming':discord.ActivityType.streaming,
				'watching':discord.ActivityType.watching,
				'listening':discord.ActivityType.listening
			}.get(mode,discord.ActivityType.unknown)
			if globals.verbose: print(mode+' command')
			if len(status)>0:
				if not globals.modules['censor']:
					await emformat.genericmsg(ctx.message.channel, "the censor module isn't running, so this command can't be used.","error",mode)
					return
				danger=self.bot.cogs['Censor'].dangerous(status)
				if danger:
					await emformat.genericmsg(ctx.message.channel,
					"can't set the status with such filthy language like `"+' ,'.join(danger)+"`","error",mode)
				else:
					await self.bot.change_presence(activity=discord.Activity(name=status,type=type))
					await emformat.genericmsg(ctx.message.channel,"status: "+mode.capitalize()+" **"+status+"**","done",mode)
					with open(globals.store+"playing.txt","w") as file:
						file.write(mode+' '+status)
			else:
				await self.bot.change_presence(activity=discord.Game(name='m/help'))
				await emformat.genericmsg(ctx.message.channel,"done!\nreset status","done",mode)
				with open(globals.store+"playing.txt","w") as file:
					file.write('')
		else:
			await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","playing")
	@playing.error
	async def playing_error(self,ctx,error):
		print(error)
		await emformat.genericmsg(ctx.message.channel,"failed to set that playing status! please try a different one.","error","playing")
	
	@commands.command(pass_context=True, no_pm=False, aliases=['say'])
	async def echo(self,ctx,*,msg=''):
		"""Repeat after me"""
		if globals.verbose: print('echo command')
		
		echo = utils.SanitizeMessage(ctx.message)
		echo = echo[echo.find('echo')+5:]
		if len(echo)>0:
			await ctx.message.channel.send(echo)

	@commands.command(pass_context=True, no_pm=False, aliases=['poll'])
	async def vote(self,ctx,*,msg=''):
		"""Hold a vote"""
		if globals.verbose: print('vote command')
		
		if re.match(r'[^.]*\?.*,.*',msg):
			if globals.modules['censor']:
				danger = self.bot.cogs['Censor'].dangerous(msg, guild=ctx.guild.id)
				if danger:
					await ctx.channel.send(self.bot.cogs['Censor'].sass()+f"\nI found these filthy words in your poll; `"+', '.join(danger)+"`")
					return
			
			cmd = list(filter(None,[x.strip(' ') for x in msg.split(' ')]))
			timelimit=time.time()+300 #5 minutes default
			if cmd[-1].isdigit():
				timelimit = time.time()+int(cmd[-1])*60
				cmd=cmd[:-1]
			
			msg = ' '.join(cmd)
			
			question = msg[:msg.find('?')+1]
			
			# initalize vote counts
			votes = {}
			for option in filter(None,msg[msg.find('?')+2:].split(',')):
				votes[' '.join(option.split())] = 0
			
			# hardcoded list of possible voting emoji
			emoji = ['🇦','🇧','🇨','🇩','🇪','🇫','🇬','🇭','🇮','🇯','🇰','🇱','🇲','🇳']
			if len(votes) > len(emoji):
				await ctx.message.channel.send(f'unfortunately, merely currently only supports up to {len(emoji)} options.')
				return
			if len(votes) <= 1:
				await ctx.message.channel.send(f"please provide more than one option.")
				return
			
			# trim emoji list to only the emoji available for voting
			emoji = emoji[:len(votes)]
			
			try:
				votemsg = await ctx.message.channel.send(f'{ctx.message.author} has started a vote.',embed=self.printvote(question,votes,timelimit,emoji))
			except Exception:
				await ctx.channel.send("failed to start vote! embed messages permission is required.")
				return
			
			try:
				for i in range(0, len(votes)):
					await votemsg.add_reaction(emoji[i])
			except Exception:
				await ctx.channel.send("failed to add reactions! cancelled vote.")
				return
			
			while timelimit - time.time() > 0:
				await asyncio.sleep(0.5)
				try:
					votemsg = await ctx.channel.fetch_message(votemsg.id)
				except:
					await ctx.channel.send("you appear to have deleted the vote, so it's cancelled.")
					return
				
				for reaction in votemsg.reactions:
					if str(reaction.emoji) in emoji:
						# update vote counts based on the number of currently active reacts
						votes[list(votes.keys())[emoji.index(str(reaction.emoji))]]=reaction.count-1
				
				# update message with new information
				await votemsg.edit(content=f'{ctx.message.author} has started a vote.',embed=self.printvote(question,votes,timelimit,emoji))
			
			# vote window has closed
			winners=[]
			for option in sorted(votes, key=votes.get, reverse=True):
				if votes[option]>=max(votes.values()):
					winners.append(f'{option} for {votes[option]} vote{"s" if votes[option]!=1 else ""}')
			if max(votes.values())>0:
				await ctx.message.channel.send(f'the vote `{question}` has ended. the winner{"s are tied at" if len(winners)!=1 else " is"}```{chr(10).join(winners)}```')
			else:
				await ctx.message.channel.send(f'the vote `{question}` has ended. there was no votes.')
		else:
			await emformat.genericmsg(ctx.message.channel,help.dhelp['vote'],'help','vote')

	@commands.command(pass_context=True, no_pm=False, aliases=['roll','diceroll'])
	async def dice(self,ctx,*args):
		"""Rolls several n sided die"""
		if not args: args=[6]
		if len(args)>32:
			await ctx.send("i will roll at most 32 dice.")
			return
		results = []
		for i,v in enumerate(args):
			counter = f"dice {i+1}"+(f", {v} sides" if len(set(args))>1 else '')+") " if len(args)>1 else ''
			n = random.choice(range(1, int(v)+1))
			results.append(f"{counter}rolled a {n}!")
		await ctx.send('\n'.join(results))
	@dice.error
	async def dice_error(self, ctx, error):
		print(error)
		await ctx.send("please use positive whole numbers only.")

	@commands.command(pass_context=True, no_pm=False, aliases=['think'])
	async def thonk(self,ctx):
		""":thinking:"""
		if globals.verbose: print('thonk command')
		await ctx.message.channel.send(random.choice(self.thonks))
	@thonk.error
	async def thonkerr(self, ctx, error):
		await ctx.channel.send("use external emojis permission is required to send thonks.")
		
	@commands.command(pass_context=True, no_pm=False, aliases=['thinkall'])
	async def thonkall(self,ctx):
		""":thinking:"""
		if globals.verbose: print('thonkall command')
		await ctx.message.channel.send('<a:thonkall:490687883716591617>')
