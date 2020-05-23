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
		
		self.bot.events['on_ready'].append(self.recover_status)
	
	def __del__(self):
		self.bot.events['on_ready'].remove(self.recover_status)
	
	async def recover_status(self):
		with open(globals.store+"playing.txt","r") as file:
			playing=file.read().split()
		if len(playing)>1:
			print('changing status to '+' '.join(playing)+'...')
			await bot.cogs['Fun'].set_status(playing[0], ' '.join(playing[1:]))
		else:
			print('no playing status found')
			await bot.cogs['Fun'].set_status()
	
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

	async def set_status(self, mode='', status=''):
		if len(status)>0:
			type = {
				'playing':discord.ActivityType.playing,
				'streaming':discord.ActivityType.streaming,
				'watching':discord.ActivityType.watching,
				'listening':discord.ActivityType.listening
			}.get(mode.lower(),discord.ActivityType.playing)
			await self.bot.change_presence(activity=discord.Activity(name=status,type=type))
			with open(globals.store+"playing.txt","w") as file:
				file.write(mode+' '+status)
		else:
			await self.bot.change_presence(activity=discord.Game(name=f"{globals.prefix_short}help"))
			with open(globals.store+"playing.txt","w") as file:
				file.write('')
	
	@commands.command(no_pm=False, aliases=['watching','streaming','listening'])
	async def playing(self, ctx, *, status=''):
		"""Command Description"""
		mode=ctx.invoked_with.lower()
		if globals.verbose: print(mode+' command')
		if len(status)>0:
			if not globals.modules['censor']:
				await emformat.genericmsg(ctx.channel, "the censor module isn't running, so this command can't be used.","error",mode)
				return
			danger=self.bot.cogs['Censor'].dangerous(status)
			if danger:
				await emformat.genericmsg(ctx.channel,
				"can't set the status with such filthy language like `"+' ,'.join(danger)+"`","error",mode)
			else:
				await self.set_status(mode, status)
				await emformat.genericmsg(ctx.channel,"status: "+mode.capitalize()+" **"+status+"**","done",mode)
		else:
			await self.set_status()
			await emformat.genericmsg(ctx.channel,"done!\nreset status","done",mode)
	@playing.error
	async def playing_error(self,ctx,error):
		print(error)
		await emformat.genericmsg(ctx.channel,"failed to set that playing status! please try a different one.","error","playing")
	
	@commands.command(no_pm=False, aliases=['say'])
	async def echo(self,ctx,*,msg=''):
		"""Repeat after me"""
		if globals.verbose: print('echo command')
		
		echo = utils.SanitizeMessage(ctx.message)
		echo = echo[echo.find('echo')+5:]
		if len(echo)>0:
			await ctx.send(echo)

	@commands.command(no_pm=False, aliases=['poll'])
	async def vote(self,ctx,*,msg=''):
		"""Hold a vote"""
		if globals.verbose: print('vote command')
		
		if re.match(r'[^.]*\?.*,.*',msg):
			if globals.modules['censor']:
				danger = self.bot.cogs['Censor'].dangerous(msg, guild=ctx.guild.id)
				if danger:
					await ctx.send(self.bot.cogs['Censor'].sass()+f"\nI found these filthy words in your poll; `"+', '.join(danger)+"`")
					return
			
			cmd = list(filter(None,[x.strip(' ') for x in msg.split(' ')]))
			if cmd[-1].isdigit() and 1<=int(cmd[-1])<=180:
				timelimit = time.time()+int(cmd[-1])*60
				cmd=cmd[:-1]
			else: t=time.time()+300 #5 minutes default
			
			msg = ' '.join(cmd)
			
			question = msg[:msg.find('?')+1]
			
			# initalize vote counts
			votes = {}
			for option in filter(None,msg[msg.find('?')+2:].split(',')):
				votes[' '.join(option.split())] = 0
			
			# hardcoded list of possible voting emoji
			emoji = ['🇦','🇧','🇨','🇩','🇪','🇫','🇬','🇭','🇮','🇯','🇰','🇱','🇲','🇳']
			if len(votes) > len(emoji):
				await ctx.send(f'unfortunately, {globals.name} currently only supports up to {len(emoji)} options.')
				return
			if len(votes) <= 1:
				await ctx.send(f"please provide more than one option.")
				return
			
			# trim emoji list to only the emoji available for voting
			emoji = emoji[:len(votes)]
			
			votemsg = await ctx.send(f'{ctx.author} has started a vote.',embed=self.printvote(question,votes,timelimit,emoji))
			
			for i in range(0, len(votes)):
				await votemsg.add_reaction(emoji[i])
			
			while timelimit - time.time() > 0:
				await asyncio.sleep(0.5)
				try:
					votemsg = await ctx.channel.fetch_message(votemsg.id)
				except:
					await ctx.send("you appear to have deleted the vote, so it's cancelled.")
					return
				
				for reaction in votemsg.reactions:
					if str(reaction.emoji) in emoji:
						# update vote counts based on the number of currently active reacts
						votes[list(votes.keys())[emoji.index(str(reaction.emoji))]]=reaction.count-1
				
				# update message with new information
				await votemsg.edit(content=f'{ctx.author} has started a vote.',embed=self.printvote(question,votes,timelimit,emoji))
			
			# vote window has closed
			winners=[]
			for option in sorted(votes, key=votes.get, reverse=True):
				if votes[option]>=max(votes.values()):
					winners.append(f'{option} for {votes[option]} vote{"s" if votes[option]!=1 else ""}')
			if max(votes.values())>0:
				await ctx.send(f'the vote `{question}` has ended. the winner{"s are tied at" if len(winners)!=1 else " is"}```{chr(10).join(winners)}```')
			else:
				await ctx.send(f'the vote `{question}` has ended. there was no votes.')
		else:
			await emformat.genericmsg(ctx.channel,help.dhelp['vote'],'help','vote')

	@commands.command(no_pm=False, aliases=['roll','diceroll'])
	async def dice(self,ctx,*args):
		"""Rolls several n sided die"""
		if not args: args=[6]
		n = -1
		for i,v in enumerate(args):
			counter = str(i+1)+") " if len(args)>1 else ''
			try:
				r = random.randint(1,int(v))
				n = r if r != n else random.randint(1,int(v))
				await ctx.send(counter+"rolled a "+str(n)+"!")
			except:
				await ctx.send(counter+"please use positive whole numbers only.")

	@commands.command(no_pm=False, aliases=['think'])
	async def thonk(self,ctx):
		""":thinking:"""
		if globals.verbose: print('thonk command')
		await ctx.send(random.choice(self.thonks))
		
	@commands.command(no_pm=False, aliases=['thinkall'])
	async def thonkall(self,ctx):
		""":thinking:"""
		if globals.verbose: print('thonkall command')
		await ctx.send('<a:thonkall:490687883716591617>')
