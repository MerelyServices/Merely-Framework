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
		
		em=discord.Embed(type='rich',inline=False,description=str,url=globals.apiurl+'#/vote')
		
		return em

	@commands.command(pass_context=True, no_pm=False, aliases=['watching','streaming','listening'])
	async def playing(self, ctx, *, status=''):
		"""Command Description"""
		mode=ctx.invoked_with.lower()
		type={
			'playing':discord.ActivityType.playing,
			'streaming':discord.ActivityType.streaming,
			'watching':discord.ActivityType.watching,
			'listening':discord.ActivityType.listening
		}.get(mode,discord.ActivityType.unknown)
		if globals.verbose: print(mode+' command')
		if len(status)>0:
			if globals.dangerous == None:
				await emformat.genericmsg(ctx.message.channel, "the censor module isn't running, so this command can't be used.","error",mode)
				return
			danger=globals.dangerous(status)
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
	@playing.error
	async def playing_error(self,ctx,error):
		print(error)
		await emformat.genericmsg(ctx.message.channel,"failed to set that playing status! please try a different one.","error","playing")
	
	# @commands.command(pass_context=True, no_pm=False, aliases=['memes','mem'])
	# async def meme(self, ctx, *, said=''):
	# 	said=said.replace('#','get ').split(' ')
	# 	if len(said)>0 and said[0]=='add': #adds more memes to the meme machine
	# 		"""if len(said)==1 or len(said[1])<10 or said[1][:4]!='http':
	# 			await ctx.message.channel.send("you need to provide a link to an image after the command!\nfor example; ```merely meme add https://cdn.discordapp.com/attachments/198337653412855808/283880728863703041/unknown.png```")
	# 			return"""
	# 		if globals.verbose: print('meme add command')
	# 		await ctx.message.channel.send("you can no longer add memes through this command, a new system will be phased in soon.")
	# 		"""meme=said[1]
	# 		meme=meme.replace("\n"," ")
	# 		with open(globals.store+'memes.txt',"r",encoding='utf8') as f:
	# 			memelist=f.readlines()
	# 		if meme+'\n' in memelist:
	# 			await ctx.message.channel.send("that meme's already on the list!")
	# 			return
	# 		lines=[]
	# 		with open(globals.store+'deadmemes.txt',"r",encoding='utf8') as f:
	# 			for line in f.readlines():
	# 				lines.append(line[:line.index('#')-1 if '#' in line else len(line)])
	# 		if meme in lines:
	# 			await ctx.message.channel.send("that's a known dead meme. you can't add memes that have been deleted back into the list.")
	# 			return
	# 		else:
	# 			with open(globals.store+'memes.txt','a',encoding='utf8') as f:
	# 				f.write(meme+"\n")
	# 			with open(globals.store+'memes.txt','r',encoding='utf8') as f:
	# 				x=len(f.readlines())
	# 			self.lastmeme[ctx.message.guild.id]=meme
	# 			await ctx.message.channel.send("i've added your meme to the list! (#"+str(x)+")")
	# 			await self.bot.get_channel(globals.modchannel).send(ctx.message.author.name+'#'+ctx.message.author.discriminator+
	# 			" just added a meme. if it's no good, `m/meme delet` it.\n#"+str(x)+': '+meme)
	# 			self.lastmeme[globals.modchannel]=meme"""
	# 	elif len(said)>0 and (said[0]=='delet' or said[0]=='delete'): #delete a broken or bad meme
	# 		if ctx.message.guild.id not in self.lastmeme or self.lastmeme[ctx.message.guild.id]==None:
	# 			await ctx.message.channel.send("i don't know what meme you're referring to, please select it first using `m/meme #<number>`.")
	# 			return
	# 		if globals.verbose: print('meme delet command')
	# 		with open(globals.store+'memes.txt',"r+",encoding='utf8') as f:
	# 			memelist=f.readlines()
	# 			f.seek(0)
	# 			deleted=[]
	# 			num=0
	# 			for i in memelist:
	# 				if i!=self.lastmeme[ctx.message.guild.id]+'\n':
	# 					f.write(i)
	# 				else:
	# 					deleted.append(num)
	# 				num+=1
	# 			f.truncate()
			
	# 		if len(deleted)!=0:
	# 			with open(globals.store+'deadmemes.txt',"a",encoding='utf8') as f:
	# 				for delet in deleted:
	# 					f.write(memelist[delet]+" #deleted by @"+ctx.message.author.name+'#'+ctx.message.author.discriminator+"\n")
				
	# 			await ctx.message.channel.send("meme deleted!")
	# 			if ctx.message.channel != globals.modchannel:
	# 				await self.bot.get_channel(globals.modchannel).send(ctx.message.author.name+'#'+ctx.message.author.discriminator+
	# 				" just deleted meme #"+str(', '.join(deleted))+". `m/lockout` the user if you think this is fraudulent.\n"+\
	# 				"*note:* only Yiays can add dead memes back, so ask him.\n"+self.lastmeme[ctx.message.guild.id])
	# 			self.lastmeme[ctx.message.guild.id]=None
			
	# 		else:
	# 			await ctx.message.channel.send("failed to delete meme!\nit's possible someone else already deleted it or there was an error.")
			
	# 	elif len(said)>0 and said[0]=='get':
	# 		if globals.verbose: print('meme get command')
	# 		if len(said)==1:
	# 			await ctx.message.channel.send(help.dhelp['meme'])
	# 			return
	# 		if said[1].isdigit(): x=round(int(said[1]))
	# 		else:
	# 			await ctx.message.channel.send("i need a valid meme number!")
	# 			return
	# 		with open(globals.store+'memes.txt','r',encoding='utf8') as f:
	# 			memelist=f.readlines()
	# 		if x>len(memelist) or x<1:
	# 			await ctx.message.channel.send("i don't have a meme by that number!")
	# 		else:
	# 			meme=memelist[x-1]
	# 			await ctx.message.channel.send("#"+str(x)+': '+meme)
	# 			self.lastmeme[ctx.message.guild.id]=meme.replace('\n','')
	# 	elif len(said)>0 and said[0]=='repeatstats':
	# 		if globals.verbose: print('meme repeatstats command')
	# 		with open(globals.store+'memes.txt','r',encoding='utf8') as f:
	# 			memelist=f.readlines()
	# 		await ctx.message.channel.send('merely has avoided repetition over the last '+str(len(self.usedmemes))+' memes, the repetition avoidance limit is '+str(math.floor(len(memelist)*0.6))+'.')
		
	# 	elif len(said)>0 and said[0]=='count':
	# 		if globals.verbose: print('meme count command')
	# 		with open(globals.store+'memes.txt','r',encoding='utf8') as f:
	# 			memecount=len(f.readlines())
	# 		await ctx.message.channel.send('merely currently has '+str(memecount)+' memes.')
	# 	else:
	# 		if globals.verbose: print('meme command')
	# 		if len(said)>0 and said[0].isdigit(): x=int(said[0])
	# 		else: x=1
	# 		if x>10:
	# 			await ctx.message.channel.send("you can't request more than 10 memes at once, if you want a meme by the #number, use `m/meme #number` instead.")
	# 		else:
	# 			with open(globals.store+'memes.txt','r',encoding='utf8') as f:
	# 				memelist=f.readlines()
	# 			for i in range(x):
	# 				chosen=random.choice(range(len(memelist)))
	# 				meme=memelist[chosen]
	# 				while meme in self.usedmemes:
	# 					chosen=random.choice(range(len(memelist)))
	# 					meme=memelist[chosen]
	# 				self.usedmemes.append(meme)
	# 				if(len(self.usedmemes)>(len(memelist)*0.6)):
	# 					self.usedmemes=self.usedmemes[-math.floor(len(memelist)*0.6):]
	# 				await ctx.message.channel.send("#"+str(chosen+1)+': '+meme)
	# 			self.lastmeme[ctx.message.guild.id]=meme.replace('\n','')
				
	# 			if random.random() < 1/30:
	# 				await emformat.make_embed(ctx.message.channel,'',title="Did you know...",
	# 					description="you can delete memes that have been sitting in the sun for too long using `m/meme delet`. this deletes the previously shown meme on the channel.",
	# 					color=0xf4e242,
	# 					author='Handy Hints with merely',
	# 					footer="merely v"+globals.ver+" - created by Yiays#5930"
	# 				)
	# 			elif random.random() < 1/30:
	# 				await emformat.make_embed(ctx.message.channel,'',title="Did you know...",
	# 					description="if you want to add a meme, just copy the link to an image and paste it at the end of a `m/meme add ` command.",
	# 					color=0xf4e242,
	# 					author='Handy Hints with merely',
	# 					footer="merely v"+globals.ver+" - created by Yiays#5930"
	# 				)

	@commands.command(pass_context=True, no_pm=False, aliases=['say'])
	async def echo(self,ctx,*,msg=''):
		"""Repeat after me"""
		if globals.verbose: print('echo command')
		
		echo = utils.SanitizeMessage(ctx.message)
		echo = echo[echo.find('echo')+5:]
		await ctx.message.channel.send(echo)

	@commands.command(pass_context=True, no_pm=False)
	async def vote(self,ctx,*,msg=''):
		"""Hold a vote"""
		if globals.verbose: print('vote command')
		
		if re.match(r'[^.]*\?.*,.*',msg):
			cmd = list(filter(None,[x.strip(' ') for x in msg.split(' ')]))
			msg = ' '.join(cmd)
			if cmd[-1].isdigit() and 1<=int(cmd[-1])<=180:
				t=time.time()+int(cmd[-1])*60
				cmd=cmd[:-1]
				msg = ' '.join(cmd)
			else: t=time.time()+300 #5 minutes default
			q=msg[:msg.find('?')+1]
			v={}
			for option in filter(None,msg[msg.find('?')+2:].split(',')):
				v[' '.join(option.split())]=0
			c=len(v)
			e=['🇦','🇧','🇨','🇩','🇪','🇫','🇬','🇭','🇮','🇯','🇰','🇱','🇲','🇳']
			if c>len(e):
				await ctx.message.channel.send(f'unfortunately, merely currently only supports up to {len(e)} options.')
				return
			e=e[:c]
			
			vote=await ctx.message.channel.send(f'{ctx.message.author} has started a vote.',embed=self.printvote(q,v,t,e))
			
			for i in range(0,c):
				await vote.add_reaction(e[i])
			
			done=False
			while not done:
				await asyncio.sleep(0.5)
				try:
					vote = await ctx.channel.fetch_message(vote.id)
				except:
					await ctx.channel.send('you appear to have deleted the vote, so it\'s cancelled.')
					return
				for reaction in vote.reactions:
					if str(reaction.emoji) in e:
						v[list(v.keys())[e.index(str(reaction.emoji))]]=reaction.count-1
				await vote.edit(content=f'{ctx.message.author} has started a vote.',embed=self.printvote(q,v,t,e))
				if t-time.time()<=0:
					winners=[]
					for option in sorted(v, key=v.get, reverse=True):
						if v[option]>=max(v.values()):
							winners.append(f'{option} for {v[option]} vote{"s" if v[option]!=1 else ""}')
					if max(v.values())>0:
						await ctx.message.channel.send(f'the vote `{q}` has ended. the winner{"s are tied at" if len(winners)!=1 else " is"}```{chr(10).join(winners)}```')
					else:
						await ctx.message.channel.send(f'the vote `{q}` has ended. there was no votes.')
					done=True
		else:
			await emformat.genericmsg(ctx.message.channel,help.dhelp['vote'],'help','vote')

	@commands.command(pass_context=True, no_pm=False, aliases=['roll','diceroll'])
	async def dice(self,ctx,*args):
		"""Rolls several n sided die"""
		if not args: args=[6]
		n = -1
		for i,v in enumerate(args):
			counter = str(i+1)+") " if len(args)>1 else ''
			try:
				r = random.randint(1,int(v))
				n = r if r != n else random.randint(1,int(v))
				await ctx.message.channel.send(counter+"rolled a "+str(n)+"!")
			except:
				await ctx.message.channel.send(counter+"please use positive whole numbers only.")

	@commands.command(pass_context=True, no_pm=False, aliases=['think'])
	async def thonk(self,ctx):
		""":thinking:"""
		if globals.verbose: print('thonk command')
		await ctx.message.channel.send(random.choice(self.thonks))
		
	@commands.command(pass_context=True, no_pm=False, aliases=['thinkall'])
	async def thonkall(self,ctx):
		""":thinking:"""
		if globals.verbose: print('thonkall command')
		await ctx.message.channel.send('<a:thonkall:490687883716591617>')
