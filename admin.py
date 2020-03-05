import globals
import asyncio
import discord
import time, os, math, re
from discord.ext import commands
import emformat, help

globals.commandlist['admin']=['welcome','farewell','janitor','die','clean','purge','logcat','servers','lockout','changelog','announceupdate','owneroptout','lockout']

class Admin(commands.Cog):
	"""Admin related commands."""
	def __init__(self, bot):
		self.bot = bot
		globals.janitor = self.janitorservice
	
	def printlist(self,list,n,limit):
		s="page "+str(n+1)+" of "+str(math.ceil(len(list)/limit))+";```"+'\n'.join(list[n*limit:min(n*limit+limit,len(list))])+"```"
		print(s)
		return s

	@commands.group(pass_context=True, no_pm=True)
	async def welcome(self,ctx):
		"""Configure the welcome message for your server."""
		globals.config.read(globals.store+'config.ini')
		if ctx.invoked_subcommand is None:
			if ctx.message.author.id not in globals.authusers and ctx.message.author.id != ctx.message.guild.owner.id:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","welcome")
				return
			await ctx.message.channel.send(help.dhelp['welcome'])
	@welcome.command(pass_context=True,name='get')
	async def welcomeget(self,ctx):
		if globals.config.get(str(ctx.message.guild.id),'welcome_message')!='':
			await ctx.message.channel.send('the welcome message is currently;\n'+globals.config.get(str(ctx.message.guild.id),'welcome_message').format('@USER',ctx.message.guild.name))
		else:
			await ctx.message.channel.send("you currently don't have a welcome message on this server.\n"+\
			"create one by going to the desired channel and typing `merely welcome Welcome, {}, to {}!`, where the first `{}` will become the name of the new user and the second `{}` will be the server name.")
	@welcome.command(pass_context=True,name='set')
	async def welcomeset(self,ctx,*,message=''):
		if ctx.message.author.id not in globals.authusers and ctx.message.author.id != ctx.message.guild.owner.id:
			await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","welcome")
			return
		if isinstance(ctx.message.channel,discord.abc.PrivateChannel):
			await ctx.message.channel.send("you need to set the welcome message in the channel that it will appear in!")
			return
		if message=='':
			await ctx.message.channel.send('in the channel where you want the alerts: `merely welcome set Welcome, {}, to {}!`, where the first `{}` will become the name of the new user and the optional second `{}` will be the server name.\nto remove the welcome message, use `merely welcome clear`.')
			return
		else:
			if str(ctx.message.guild.id) not in globals.config:
				globals.config.add_section(str(ctx.message.guild.id))
			globals.config.set(str(ctx.message.guild.id),'welcome_channel',str(ctx.message.channel.id))
			globals.config.set(str(ctx.message.guild.id),'welcome_message',message)
			globals.save()
			await ctx.message.channel.send("successfully set the welcome message!")
	@welcome.command(pass_context=True,name='clear')
	async def welcomeclear(self,ctx):
		if ctx.message.author.id not in globals.authusers and ctx.message.author.id != ctx.message.guild.owner.id:
			await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","welcome")
			return
		if str(ctx.message.guild.id) not in globals.config.sections() or globals.config.get(str(ctx.message.guild.id),'welcome_message')=='':
			await ctx.message.channel.send("you currently don't have a welcome message on this server.")
		else:
			globals.config.set(str(ctx.message.guild.id),'welcome_message','')
			globals.save()
			await ctx.message.channel.send("removed and disabled the welcome message!")
	
	@commands.group(pass_context=True, no_pm=True)
	async def farewell(self,ctx):
		"""Configure the farewell message for your server. Not obsolete, just can't be in the same script as m/welcome"""
		globals.config.read(globals.store+'config.ini')
		if ctx.invoked_subcommand is None:
			if ctx.message.author.id not in globals.authusers and ctx.message.author.id != ctx.message.guild.owner.id:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","farewell")
				return
			await ctx.message.channel.send(help.dhelp['farewell'])
	@farewell.command(pass_context=True,name='get')
	async def farewellget(self,ctx):
		if globals.config.get(str(ctx.message.guild.id),'farewell_message')!='':
			await ctx.message.channel.send('the farewell message is currently;\n'+globals.config.get(str(ctx.message.guild.id),'farewell_message').format('USER#1234'))
		else:
			await ctx.message.channel.send("you currently don't have a farewell message on this server.\n"+\
			"create one by going to the desired channel and typing `merely farewell {} has left the server!`, where `{}` will become the name of the departed user.")
	@farewell.command(pass_context=True,name='set')
	async def farewellset(self,ctx,*,message=''):
		if ctx.message.author.id not in globals.authusers and ctx.message.author.id != ctx.message.guild.owner.id:
			await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","farewell")
			return
		if isinstance(ctx.message.channel,discord.abc.PrivateChannel):
			await ctx.message.channel.send("sorry, you need to set the farewell message in the channel that it will appear in!")
			return
		if message=='':
			await ctx.message.channel.send('in the channel where you want the alerts: `merely farewell set {} has left the server!`, where `{}` will become the name of the departed user. to remove the farewell message, use `merely farewell clear`.')
			return
		else:
			if str(ctx.message.guild.id) not in globals.config:
				globals.config.add_section(str(ctx.message.guild.id))
			globals.config.set(str(ctx.message.guild.id),'farewell_channel',str(ctx.message.channel.id))
			globals.config.set(str(ctx.message.guild.id),'farewell_message',message)
			globals.save()
			await ctx.message.channel.send("successfully set the farewell message!")
	@farewell.command(pass_context=True,name='clear')
	async def farewellclear(self,ctx):
		if ctx.message.author.id not in globals.authusers and ctx.message.author.id != ctx.message.guild.owner.id:
			await ctx.message.channel.send('this command is restricted.')
			return
		if str(ctx.message.guild.id) not in globals.config.sections() or globals.config.get(str(ctx.message.guild.id),'farewell_message')=='':
			await ctx.message.channel.send("you currently don't have a farewell message on this server.")
		else:
			globals.config.set(str(ctx.message.guild.id),'farewell_message','')
			globals.save()
			await ctx.message.channel.send("removed and disabled the farewell message!")
	
	async def janitorservice(self,msg):
		if str(msg.channel.id) in globals.config.get('janitor','strict',fallback='').split(' '):
			await asyncio.sleep(30)
			try:
				await msg.delete()
			except Exception as e:
				print(e)
				return
		elif str(msg.channel.id) in globals.config.get('janitor','relaxed',fallback='').split(' '):
			if msg.author==self.bot.user or self.bot.user in msg.mentions or msg.content.lower().startswith('m/') or msg.content.lower().startswith('merely'):
				await asyncio.sleep(30)
				try:
					await msg.delete()
				except Exception as e:
					print(e)
					return
	
	@commands.group(pass_context=True, no_pm=False)
	async def janitor(self,ctx):
		"""Configure the janitor for your channel."""
		globals.config.read(globals.store+'config.ini')
		if ctx.invoked_subcommand is None:
			if ctx.message.author.id not in globals.authusers and ctx.message.author.id != ctx.message.guild.owner.id:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","janitor")
				return
			await ctx.message.channel.send(help.dhelp['janitor'])
	@janitor.command(pass_context=True,name='join')
	async def janitorjoin(self,ctx,mode=''):
		if ctx.message.author.id not in globals.authusers and ctx.message.author.id != ctx.message.guild.owner.id:
			await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","janitor")
			return
		if str(ctx.message.channel.id) in globals.config.get('janitor','strict').split(' ') or str(ctx.message.channel.id) in globals.config.get('janitor','relaxed').split(' '):
			await ctx.message.channel.send("this channel has already opted into the janitor service!")
		elif mode not in ['strict','relaxed']:
			await ctx.message.channel.send('you must specify whether you want a strict janitor or a relaxed janitor.\n*strict*; all messages from everyone are deleted after 30 seconds.\n*relaxed*; messages to and from merely are deleted after 30 seconds.')
		else:
			globals.config.set('janitor',mode,globals.config.get('janitor',mode)+' '+str(ctx.message.channel.id))
			globals.save()
			await ctx.message.channel.send('opted in to janitor!')
	@janitor.command(pass_context=True,name='leave')
	async def janitorleave(self,ctx):
		if ctx.message.author.id not in globals.authusers and ctx.message.author.id != ctx.message.guild.owner.id:
			await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","janitor")
			return
		mode=''
		if str(ctx.message.channel.id) in globals.config.get('janitor','strict').split(' '):
			mode='strict'
		elif str(ctx.message.channel.id) in globals.config.get('janitor','relaxed').split(' '):
			mode='relaxed'
		else:
			await ctx.message.channel.send("this channel hasn't opted in to the janitor service!")
		if mode in ['strict','relaxed']:
			t=globals.config.get('janitor',mode).split(' ')
			t.remove(str(ctx.message.channel.id))
			t=' '.join(t)
			globals.config.set('janitor',mode,t)
			globals.save()
			await ctx.message.channel.send("successfully opted out of janitor!")
	
	@commands.command(pass_context=True, no_pm=False)
	async def die(self, ctx):
		"""Shut down the bot for 30 seconds"""
		if globals.verbose: print('die command')
		if ctx.message.author.id in globals.authusers:
			#await emformat.genericmsg(ctx.message.channel,"shutting down...","bye","die")
			await emformat.make_embed(ctx.message.channel, "", "merely die", "shutting down...", image="https://media.discordapp.net/attachments/302695523360440322/685087322844299284/tenor.gif", footer="merely v"+globals.ver+" - created by Yiays#5930", icon=globals.iconurl, link=globals.apiurl+"#/die")
			with open(globals.store+'alive.txt','w') as f:
				f.write(str(ctx.message.channel.id))
			if globals.modules['webserver']: await globals.modules["webserver"].stop()
			await self.bot.logout()
		else:
			await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","die")
		return True
	
	@commands.command(pass_context=True, no_pm=True, aliases=['clear'])
	async def clean(self,ctx,n=50,strict=''):
		"""Purge the channel of bot related messages"""
		if globals.verbose: print('clean command')
		if ctx.message.author.id in globals.authusers or ctx.message.author.id == ctx.message.guild.owner.id:
			if strict=='strict':
				def is_delete(m):
					return True
			else:
				def is_delete(m):
					return (len(m.content)>0 and m.content.lower().startswith('merely')) or m.content.lower().startswith('m/') or self.bot.user in m.mentions or m.author==self.bot.user or m.author==self.bot.get_user(265286478668496896) or len(m.content)==1 or m.type==discord.MessageType.pins_add
			
			try:
				n=int(n)
			except:
				n=50
			if n>100:
				await ctx.message.channel.send('clearing more than 100 messages at once may take several minutes as merely will be rate-limited. continue? (reply with a clear `yes` within 30 seconds)')
				def check(m):
					return m.content.lower()=='yes' and m.channel==ctx.message.channel and m.author==ctx.message.author
				try:
					await self.bot.wait_for('message', check=check, timeout=30)
				except asyncio.TimeoutError:
					await ctx.message.channel.send('clear cancelled.')
					return
				await ctx.message.channel.send('clearing... merely may be unresponsive for a while...')
			
			deleted = await ctx.message.channel.purge(limit=n, check=is_delete)
			await emformat.genericmsg(ctx.message.channel,str(len(deleted))+' messages deleted from '+ctx.message.channel.name+'.','result','clean')
		else:
			await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","clean")
	@clean.error
	async def clean_failed(self,ctx,error):
		print(error)
		await emformat.genericmsg(ctx.message.channel,globals.apiurl+'#/clear_failed\nunable to delete messages because some of limitations in the discord api.\nvisit the website in order to get a list of solutions you can try.','error','clean')
	
	@commands.command(pass_context=True, no_pm=True)
	async def purge(self,ctx,start=0,end=0,n=100):
		"""Purge the channel of bot related messages"""
		if globals.verbose: print('purge command')
		if ctx.message.author.id in globals.superusers or ctx.message.author.id == ctx.message.guild.owner.id:
			try:
				n=int(n)
			except:
				n=100
			try:
				start=int(start)
			except:
				start=0
			try:
				end=int(end)
			except:
				end=0
			
			if start==0 or end==0:
				await ctx.message.channel.send("you must enable developer mode and copy the IDs of the first and last message to be purged.\noptionally, set an absolute number of messages to scan.")
			if n<1 or n>1000:
				await ctx.message.channel.send("scan range must be between 1 and 1000!")
			if start>end:
				start, end = end, start
			
			def is_purgerange(m):
				if m.id>=start and m.id<=end:
					return True
				return False
			
			deleted = await ctx.message.channel.purge(limit=n, check=is_purgerange)
			await emformat.genericmsg(ctx.message.channel,str(len(deleted))+' messages deleted from '+ctx.message.channel.name+'.','result','purge')
		else:
			await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","purge")
	@purge.error
	async def purge_failed(self,ctx,error):
		print(error)
		await emformat.genericmsg(ctx.message.channel,globals.apiurl+'#/clear_failed\nunable to delete messages because some of limitations in the discord api.\nvisit the website in order to get a list of solutions you can try.','error','purge')

	@commands.command(pass_context=True, no_pm=False, aliases=['log'])
	async def logcat(self,ctx,n=20):
		"""Return the last n lines from the log."""
		if globals.verbose: print('logcat command')
		if ctx.message.author.id in globals.superusers or ctx.message.author.id == ctx.message.guild.owner.id:
			if os.path.isfile(globals.store+"logs/merely-"+globals.ver+"-"+time.strftime("%d-%m-%y")+".log"):
				loglines=[]
				for _, line in zip(range(n),reversed(list(open(globals.store+"logs/merely-"+globals.ver+"-"+time.strftime("%d-%m-%y")+".log", "r", encoding='utf-8')))):
					loglines.insert(0,line)
			else:
				await ctx.message.channel.send("I don't appear to have a log...")
			await ctx.message.channel.send("here's the most recent "+str(n)+" lines in the log...```"+"".join(loglines)+"```")
		else:
			await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","logcat")
	@logcat.error
	async def logcat_error(self,ctx,error):
		print(error)
		await emformat.genericmsg(ctx.message.channel,"can't send more than 2000 characters!","error","logcat")
	
	@commands.command(pass_context=True, no_pm=False)
	async def servers(self, ctx):
		"""Return list of servers"""
		
		page=0
		servers=sorted(self.bot.guilds,key=lambda x: len(x.members), reverse=True)
		
		msg = await ctx.message.channel.send(self.printlist([s.name+' ('+str(s.id)+') - '+str(len(s.members))+' members.' for s in servers],page,10))
		await msg.add_reaction("\U000025C0") #reverse symbol
		await msg.add_reaction("\U000025B6") #play symbol
		
		def check(reaction,user):
			return str(reaction.emoji) in ["\U000025C0","\U000025B6"] and not user.bot
		
		while True:
			try:
				reaction, user = await self.bot.wait_for('reaction_add',timeout=300,check=check)
			except asyncio.TimeoutError:
				await msg.edit(content="interactive server list expired. type `m/servers` again.")
				await msg.clear_reactions()
				break
			else:
				page = page+1 if reaction.emoji=="\U000025B6" else page-1
				if page in range(math.ceil(len(servers)/10)):
					await msg.edit(content=self.printlist([s.name+' ('+str(s.id)+') - '+str(len(s.members))+' members.' for s in servers],page,10))
				else:
					page = sorted((0, page, math.ceil(len(servers)/10)))[1]
				await msg.remove_reaction(reaction.emoji,user)
		
	
	@commands.command(pass_context=True, no_pm=True)
	async def lockout(self,ctx,author='',sentence='30'):
		"""Lock a user out from being able to interact with merely."""
		print('lockout command')
		if ctx.message.author.id in globals.authusers or ctx.message.author.id == ctx.message.guild.owner.id:
			pattern = re.compile(".*#[0-9]{4}")
			if pattern.match(author):
				for g in self.bot.guilds:
					user = g.get_member_named(author)
					if user is not None:
						break
				if user is None:
					return await ctx.message.channel.send("unable to find any user with that username and discriminator!")
				uid = str(user.id)
				sentence=int(sentence)
				if sentence==0:
					globals.lockout[uid]=str(round(time.time())+2678400)
					await ctx.message.channel.send("locked out user "+author+" for a month.")
				else:
					globals.lockout[uid]=str(round(time.time())+(int(sentence)*60))
					await ctx.message.channel.send("locked out user "+author+" for "+str(sentence)+" minutes.")
				globals.save()
			else:
				await ctx.message.channel.send(help.dhelp['lockout'])
		else:
			await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","lockout")

	@commands.group(pass_context=True, no_pm=False, aliases=['changes','updates','update','change','upgrade','upgrades','improvements'])
	async def changelog(self,ctx):
		"""List changes in bot since last update."""
		if ctx.invoked_subcommand is None:
			print('changelog command')
			try:
				await ctx.message.channel.send("You can view the full changelog online! ( "+globals.apiurl+"changes.html )")
				await emformat.genericmsg(ctx.message.channel,"*here's a list of recent changes to merely...*\n\n"+''.join(globals.changes[-10:])+"\n\nremeber to leave feedback with `m/feedback` if you want changes made!",'done','changelog')
			except:
				if len(''.join(globals.changes))>=1800:
					await emformat.genericmsg(ctx.message.channel,"the changelog is too long for discord! either [view the changelog online]("+globals.apiurl+"changes.html) or check back later when it's been shortened.",'error','changelog')
					if globals.feedbackchannel: await self.bot.get_channel(globals.feedbackchannel).send("<@!140297042709708800>, the changelog is too long! ("+str(len('\n'.join(globals.changes)))+")")
	@changelog.command(pass_context=True, name='add')
	async def changelogadd(self,ctx,*,text=None):
		"""Add an entry to the changelog"""
		print('changelog add command')
		if ctx.message.author.id in globals.superusers:
			if text:
				globals.changes.extend(['\n'+t for t in '\n'.split(text)])
				globals.save()
				await ctx.message.channel.send("Appended to the changelog successfully!")
		else:
			await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","changelog")
	
	@commands.command(pass_context=True, no_pm=False)
	async def announceupdate(self,ctx,*,msg=''):
		"""Announces updates to the server owners."""
		print('announcetoserverowner command')
		if ctx.message.author.id in globals.superusers:
			if len(msg)>3:
				async with ctx.message.channel.typing():
					sent=[]
					failed=0
					ignored=0
					for s in self.bot.guilds:
						if s.owner.id not in sent and s.owner.id not in globals.owneroptout:
							try:
								await emformat.genericmsg(s.owner,"*hey there, server owner, merely's just been updated so here's a list of recent changes...*\n\n"+msg,'done','changelog')
								await s.owner.send("for more information, please visit "+globals.apiurl+"#/serverowner .\n\n"+\
									"*note: remember to use `merely feedback` to provide feedback.*\n\nif you don't want to recieve these messages, please type `m/owneroptout`.")
								sent.append(s.owner.id)
							except:
								failed+=1
						else:
							ignored+=1
					
					await ctx.message.channel.send('sent patch notes to '+str(len(sent))+' server owners successfully! `'+str(failed)+' failed, '+str(ignored)+' ignored.`')
			else:
				await ctx.message.channel.send('patch notes are required!')
		else:
			await emformat.genericmsg(ctx.message.channel,"this command is **super** restricted.","error","announcetoserverowner")
	
	@commands.command(pass_context=True, no_pm=False)
	async def owneroptout(self,ctx):
		"""Allows server owners to unsubscribe from all update news."""
		print('owneroptout command')
		if ctx.message.author.id in [s.owner.id for s in self.bot.guilds]:
			if ctx.message.author.id not in globals.owneroptout:
				globals.owneroptout.append(ctx.message.author.id)
				globals.save()
				msg = await ctx.message.channel.send('done! you will no longer get server owner-related PMs. if you wish to undo this, you will need to PM Yiays#5930')
				await msg.pin()
			else:
				await ctx.message.channel.send("you've already opted out!")
		else:
			await ctx.message.channel.send('you don\'t appear to be a server owner!')
