import globals
import asyncio
import discord
import time, os, math, re
from discord.ext import commands
import emformat, help

# ['admin']=['welcome','farewell','janitor','die','clean','purge','logcat','servers','lockout','changelog','announceupdate','owneroptout','lockout']

class Admin(commands.Cog):
	"""Admin related commands."""
	def __init__(self, bot):
		self.bot = bot
		
		self.bot.events['on_ready'].append(self.undead)
		self.bot.events['on_member_join'].append(self.welcome_member)
		self.bot.events['on_member_remove'].append(self.farewell_member)
		self.bot.events['on_message'].append(self.janitorservice)
		self.bot.events['on_guild_join'].append(self.send_ownerintro)
	
	def __del__(self):
		self.bot.events['on_ready'].remove(self.undead)
		self.bot.events['on_member_join'].remove(self.welcome_member)
		self.bot.events['on_member_remove'].remove(self.farewell_member)
		self.bot.events['on_message'].remove(self.janitorservice)
		self.bot.events['on_guild_join'].remove(self.send_ownerintro)
	
	def printlist(self,list,n,limit):
		s="page "+str(n+1)+" of "+str(math.ceil(len(list)/limit))+";```"+'\n'.join(list[n*limit:min(n*limit+limit,len(list))])+"```"
		print(s)
		return s

	@commands.group(no_pm=True, aliases=['hello', 'hi'])
	async def welcome(self,ctx):
		"""Configure the welcome message for your server."""
		globals.config.read(globals.store+'config.ini')
		if ctx.invoked_subcommand is None:
			if ctx.author.id not in globals.authusers and ctx.author.id != ctx.guild.owner.id:
				await emformat.genericmsg(ctx.channel,"this command is restricted.","error","welcome")
				return
			await ctx.send(help.dhelp['welcome'])
	@welcome.command(name='get')
	async def welcomeget(self,ctx):
		if globals.config.get(str(ctx.guild.id),'welcome_message')!='':
			await ctx.send('the welcome message is currently;\n'+globals.config.get(str(ctx.guild.id),'welcome_message').format('@USER',ctx.guild.name))
		else:
			await ctx.send("you currently don't have a welcome message on this server.\n"+\
			"create one by going to the desired channel and typing `"+(globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short)+"welcome Welcome, {}, to {}!`, where the first `{}` will become the name of the new user and the second `{}` will be the server name.")
	@welcome.command(name='set')
	async def welcomeset(self,ctx,*,message=''):
		if ctx.author.id not in globals.authusers and ctx.author.id != ctx.guild.owner.id:
			await emformat.genericmsg(ctx.channel,"this command is restricted.","error","welcome")
			return
		if isinstance(ctx.channel,discord.abc.PrivateChannel):
			await ctx.send("you need to set the welcome message in the channel that it will appear in!")
			return
		if message=='':
			await ctx.send('in the channel where you want the alerts: `'+(globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short)+'welcome set Welcome, {}, to {}!`, where the first `{}` will become the name of the new user and the optional second `{}` will be the server name.\nto remove the welcome message, use `'+(globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short)+'welcome clear`.')
			return
		else:
			if str(ctx.guild.id) not in globals.config:
				globals.config.add_section(str(ctx.guild.id))
			globals.config.set(str(ctx.guild.id),'welcome_channel',str(ctx.channel.id))
			globals.config.set(str(ctx.guild.id),'welcome_message',message)
			globals.save()
			await ctx.send("successfully set the welcome message!")
	@welcome.command(name='clear')
	async def welcomeclear(self,ctx):
		if ctx.author.id not in globals.authusers and ctx.author.id != ctx.guild.owner.id:
			await emformat.genericmsg(ctx.channel,"this command is restricted.","error","welcome")
			return
		if str(ctx.guild.id) not in globals.config.sections() or globals.config.get(str(ctx.guild.id),'welcome_message')=='':
			await ctx.send("you currently don't have a welcome message on this server.")
		else:
			globals.config.set(str(ctx.guild.id),'welcome_message','')
			globals.save()
			await ctx.send("removed and disabled the welcome message!")
	
	async def welcome_member(self, member):
		if member.id == self.bot.user.id:
			return
		globals.config.read(globals.store+'config.ini')
		if str(member.guild.id) in globals.config.sections() and globals.config.get(str(member.guild.id),'welcome_message') != '':
			await bot.get_channel(int(globals.config.get(str(member.guild.id),'welcome_channel'))).send(globals.config.get(str(member.guild.id),'welcome_message').format('<@!'+str(member.id)+'>',member.guild.name))
	
	@commands.group(no_pm=True, aliases=['goodbye', 'bye'])
	async def farewell(self,ctx):
		"""Configure the farewell message for your server. Not obsolete, just can't be in the same script as m/welcome"""
		globals.config.read(globals.store+'config.ini')
		if ctx.invoked_subcommand is None:
			if ctx.author.id not in globals.authusers and ctx.author.id != ctx.guild.owner.id:
				await emformat.genericmsg(ctx.channel,"this command is restricted.","error","farewell")
				return
			await ctx.send(help.dhelp['farewell'])
	@farewell.command(name='get')
	async def farewellget(self,ctx):
		if globals.config.get(str(ctx.guild.id),'farewell_message')!='':
			await ctx.send('the farewell message is currently;\n'+globals.config.get(str(ctx.guild.id),'farewell_message').format('USER#1234'))
		else:
			await ctx.send("you currently don't have a farewell message on this server.\n"+\
			"create one by going to the desired channel and typing `"+(globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short)+"farewell {} has left the server!`, where `{}` will become the name of the departed user.")
	@farewell.command(name='set')
	async def farewellset(self,ctx,*,message=''):
		if ctx.author.id not in globals.authusers and ctx.author.id != ctx.guild.owner.id:
			await emformat.genericmsg(ctx.channel,"this command is restricted.","error","farewell")
			return
		if isinstance(ctx.channel,discord.abc.PrivateChannel):
			await ctx.send("sorry, you need to set the farewell message in the channel that it will appear in!")
			return
		if message=='':
			await ctx.send('in the channel where you want the alerts: `'+(globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short)+'farewell set {} has left the server!`, where `{}` will become the name of the departed user. to remove the farewell message, use `'+(globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short)+'farewell clear`.')
			return
		else:
			if str(ctx.guild.id) not in globals.config:
				globals.config.add_section(str(ctx.guild.id))
			globals.config.set(str(ctx.guild.id),'farewell_channel',str(ctx.channel.id))
			globals.config.set(str(ctx.guild.id),'farewell_message',message)
			globals.save()
			await ctx.send("successfully set the farewell message!")
	@farewell.command(name='clear')
	async def farewellclear(self,ctx):
		if ctx.author.id not in globals.authusers and ctx.author.id != ctx.guild.owner.id:
			await ctx.send('this command is restricted.')
			return
		if str(ctx.guild.id) not in globals.config.sections() or globals.config.get(str(ctx.guild.id),'farewell_message')=='':
			await ctx.send("you currently don't have a farewell message on this server.")
		else:
			globals.config.set(str(ctx.guild.id),'farewell_message','')
			globals.save()
			await ctx.send("removed and disabled the farewell message!")
	
	async def farewell_member(self, member):
		if member.id == bot.user.id:
			return
		globals.config.read(globals.store+'config.ini')
		if str(member.guild.id) in globals.config.sections() and globals.config.get(str(member.guild.id),'farewell_message') != '':
			await bot.get_channel(int(globals.config.get(str(member.guild.id),'farewell_channel'))).send(globals.config.get(str(member.guild.id),'farewell_message').format(member.name+'#'+str(member.discriminator)))
	
	async def janitorservice(self,msg):
		if str(msg.channel.id) in globals.config.get('janitor','strict',fallback='').split(' '):
			await asyncio.sleep(30)
			try:
				await msg.delete()
			except Exception as e:
				print(e)
				return
		elif str(msg.channel.id) in globals.config.get('janitor','relaxed',fallback='').split(' '):
			if msg.author==self.bot.user or self.bot.user in msg.mentions or msg.content.lower().startswith(globals.prefix_short) or msg.content.lower().startswith(globals.prefix_long):
				await asyncio.sleep(30)
				try:
					await msg.delete()
				except Exception as e:
					print(e)
					return
	
	@commands.group(no_pm=False)
	async def janitor(self,ctx):
		"""Configure the janitor for your channel."""
		globals.config.read(globals.store+'config.ini')
		if ctx.invoked_subcommand is None:
			if ctx.author.id not in globals.authusers and ctx.author.id != ctx.guild.owner.id:
				await emformat.genericmsg(ctx.channel,"this command is restricted.","error","janitor")
				return
			await ctx.send(help.dhelp['janitor'])
	@janitor.command(name='join')
	async def janitorjoin(self,ctx,mode=''):
		if ctx.author.id not in globals.authusers and ctx.author.id != ctx.guild.owner.id:
			await emformat.genericmsg(ctx.channel,"this command is restricted.","error","janitor")
			return
		if str(ctx.channel.id) in globals.config.get('janitor','strict').split(' ') or str(ctx.channel.id) in globals.config.get('janitor','relaxed').split(' '):
			await ctx.send("this channel has already opted into the janitor service!")
		elif mode not in ['strict','relaxed']:
			await ctx.send(f"you must specify whether you want a strict janitor or a relaxed janitor.\n*strict*; all messages from everyone are deleted after 30 seconds.\n*relaxed*; messages to and from {globals.name} are deleted after 30 seconds.")
		else:
			globals.config.set('janitor',mode,globals.config.get('janitor',mode)+' '+str(ctx.channel.id))
			globals.save()
			await ctx.send('opted in to janitor!')
	@janitor.command(name='leave')
	async def janitorleave(self,ctx):
		if ctx.author.id not in globals.authusers and ctx.author.id != ctx.guild.owner.id:
			await emformat.genericmsg(ctx.channel,"this command is restricted.","error","janitor")
			return
		mode=''
		if str(ctx.channel.id) in globals.config.get('janitor','strict').split(' '):
			mode='strict'
		elif str(ctx.channel.id) in globals.config.get('janitor','relaxed').split(' '):
			mode='relaxed'
		else:
			await ctx.send("this channel hasn't opted in to the janitor service!")
		if mode in ['strict','relaxed']:
			t=globals.config.get('janitor',mode).split(' ')
			t.remove(str(ctx.channel.id))
			t=' '.join(t)
			globals.config.set('janitor',mode,t)
			globals.save()
			await ctx.send("successfully opted out of janitor!")
	
	@commands.command(no_pm=False)
	async def die(self, ctx):
		"""Shut down the bot for 30 seconds"""
		if globals.verbose: print('die command')
		if ctx.author.id in globals.authusers:
			#await emformat.genericmsg(ctx.channel,"shutting down...","bye","die")
			await emformat.make_embed(ctx.channel, "", f"{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}die", "shutting down...", image="https://media.discordapp.net/attachments/302695523360440322/685087322844299284/tenor.gif", footer=f"{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short} v"+globals.ver+" - created by Yiays#5930", footer_icon=globals.iconurl, link=globals.apiurl+"#/die")
			with open(globals.store+'alive.txt','w') as f:
				f.write(str(ctx.channel.id))
			if globals.modules['webserver']:
				await self.bot.cogs["Webserver"].stop()
			await self.bot.logout()
		else:
			await emformat.genericmsg(ctx.channel,"this command is restricted.","error","die")
		return True
	
	async def undead(self):
		with open(globals.store+'alive.txt','r') as f:
			try:
				id=int(f.read())
			except:
				id=False
		if id:
			print('informing channel '+str(id)+' of my return...')
			await emformat.genericmsg(self.bot.get_channel(id),"i have returned.","greet","die")
		with open(globals.store+'alive.txt','w') as f:
			f.write('')
	
	@commands.command(no_pm=True, aliases=['clear'])
	async def clean(self,ctx,n=50,strict=''):
		"""Purge the channel of bot related messages"""
		if globals.verbose: print('clean command')
		if ctx.author.id in globals.authusers or ctx.author.id == ctx.guild.owner.id:
			if strict=='strict':
				def is_delete(m):
					return True
			else:
				def is_delete(m):
					return (len(m.content)>0 and m.content.lower().startswith(globals.prefix_long)) or m.content.lower().startswith(globals.prefix_short) or self.bot.user in m.mentions or m.author==self.bot.user or m.author==self.bot.get_user(265286478668496896) or len(m.content)==1 or m.type==discord.MessageType.pins_add
			
			try:
				n=int(n)
			except:
				n=50
			if n>100:
				await ctx.send(f"clearing more than 100 messages at once may take several minutes as {globals.name} will be rate-limited. continue? (reply with a clear `yes` within 30 seconds)")
				def check(m):
					return m.content.lower()=='yes' and m.channel==ctx.channel and m.author==ctx.author
				try:
					msg = await self.bot.wait_for('message', check=check, timeout=30)
					await msg.delete()
				except asyncio.TimeoutError:
					await ctx.send('clear cancelled.')
					return
				await ctx.send(f"clearing... {globals.name} may be unresponsive for a while...")
				await asyncio.sleep(1)
			
			deleted = await ctx.channel.purge(limit=n, check=is_delete)
			await emformat.genericmsg(ctx.channel,str(len(deleted))+' messages deleted from '+ctx.channel.name+'.','result','clean')
		else:
			await emformat.genericmsg(ctx.channel,"this command is restricted.","error","clean")
	@clean.error
	async def clean_failed(self,ctx,error):
		print(error)
		await emformat.genericmsg(ctx.channel,globals.apiurl+'#/clear_failed\nunable to delete messages because some of limitations in the discord api.\nvisit the website in order to get a list of solutions you can try.','error','clean')
	
	@commands.command(no_pm=True)
	async def purge(self,ctx,start=0,end=0,n=100):
		"""Purge the channel of bot related messages"""
		if globals.verbose: print('purge command')
		if ctx.author.id in globals.superusers or ctx.author.id == ctx.guild.owner.id:
			n=int(n) if n.isdigit() else 100
			start=int(start) if start.isdigit() else 0
			end=int(end) if end.isdigit() else 0
			
			if start==0 or end==0:
				await ctx.send("you must enable developer mode and copy the IDs of the first and last message to be purged.\noptionally, set an absolute number of messages to scan.")
			if n<1 or n>1000:
				await ctx.send("scan range must be between 1 and 1000!")
			if start>end:
				start, end = end, start
			
			def is_purgerange(m):
				if m.id>=start and m.id<=end:
					return True
				return False
			
			deleted = await ctx.channel.purge(limit=n, check=is_purgerange)
			await emformat.genericmsg(ctx.channel,str(len(deleted))+' messages deleted from '+ctx.channel.name+'.','result','purge')
		else:
			await emformat.genericmsg(ctx.channel,"this command is restricted.","error","purge")
	@purge.error
	async def purge_failed(self,ctx,error):
		print(error)
		await emformat.genericmsg(ctx.channel,globals.apiurl+'#/clear_failed\nunable to delete messages because some of limitations in the discord api.\nvisit the website in order to get a list of solutions you can try.','error','purge')

	@commands.command(no_pm=False, aliases=['log'])
	async def logcat(self,ctx,n=20):
		"""Return the last n lines from the log."""
		if globals.verbose: print('logcat command')
		if ctx.author.id in globals.superusers or ctx.author.id == ctx.guild.owner.id:
			if os.path.isfile(globals.store+"logs/merely-"+globals.ver+"-"+time.strftime("%d-%m-%y")+".log"):
				loglines=[]
				for _, line in zip(range(n),reversed(list(open(globals.store+"logs/merely-"+globals.ver+"-"+time.strftime("%d-%m-%y")+".log", "r", encoding='utf-8')))):
					loglines.insert(0,line)
			else:
				await ctx.send("I don't appear to have a log...")
			await ctx.send("here's the most recent "+str(n)+" lines in the log...```"+"".join(loglines)+"```")
		else:
			await emformat.genericmsg(ctx.channel,"this command is restricted.","error","logcat")
	@logcat.error
	async def logcat_error(self,ctx,error):
		print(error)
		await emformat.genericmsg(ctx.channel,"can't send more than 2000 characters!","error","logcat")
	
	@commands.command(no_pm=False)
	async def servers(self, ctx):
		"""Return list of servers"""
		
		page=0
		servers=sorted(self.bot.guilds,key=lambda x: len(x.members), reverse=True)
		
		msg = await ctx.send(self.printlist([s.name+' ('+str(s.id)+') - '+str(len(s.members))+' members.' for s in servers],page,10))
		await msg.add_reaction("\U000025C0") #reverse symbol
		await msg.add_reaction("\U000025B6") #play symbol
		
		def check(reaction,user):
			return str(reaction.emoji) in ["\U000025C0","\U000025B6"] and not user.bot
		
		while True:
			try:
				reaction, user = await self.bot.wait_for('reaction_add',timeout=300,check=check)
			except asyncio.TimeoutError:
				await msg.edit(content=f"interactive server list expired. type `{globals.prefix_short}servers` again.")
				await msg.clear_reactions()
				break
			else:
				page = page+1 if reaction.emoji=="\U000025B6" else page-1
				if page in range(math.ceil(len(servers)/10)):
					await msg.edit(content=self.printlist([s.name+' ('+str(s.id)+') - '+str(len(s.members))+' members.' for s in servers],page,10))
				else:
					page = sorted((0, page, math.ceil(len(servers)/10)))[1]
				await msg.remove_reaction(reaction.emoji,user)
		
	
	@commands.command(no_pm=True)
	async def lockout(self,ctx,author='',sentence='30'):
		"""Lock a user out from being able to interact with merely."""
		print('lockout command')
		if ctx.author.id in globals.authusers or ctx.author.id == ctx.guild.owner.id:
			pattern = re.compile(".*#[0-9]{4}")
			if pattern.match(author):
				for g in self.bot.guilds:
					user = g.get_member_named(author)
					if user is not None:
						break
				if user is None:
					return await ctx.send("unable to find any user with that username and discriminator!")
				uid = str(user.id)
				sentence=int(sentence)
				if sentence==0:
					globals.lockout[uid]=str(round(time.time())+2678400)
					await ctx.send("locked out user "+author+" for a month.")
				else:
					globals.lockout[uid]=str(round(time.time())+(int(sentence)*60))
					await ctx.send("locked out user "+author+" for "+str(sentence)+" minutes.")
				globals.save()
			else:
				await ctx.send(help.dhelp['lockout'])
		else:
			await emformat.genericmsg(ctx.channel,"this command is restricted.","error","lockout")

	@commands.group(no_pm=False, aliases=['changes','updates','update','change','upgrade','upgrades','improvements'])
	async def changelog(self,ctx):
		"""List changes in bot since last update."""
		if ctx.invoked_subcommand is None:
			print('changelog command')
			try:
				await ctx.send("You can view the full changelog online! ( "+globals.apiurl+"changes.html )")
				await emformat.genericmsg(ctx.channel,f"*here's a list of recent changes to {globals.name}...*\n\n{''.join(globals.changes[-10:])}\n\nremeber to leave feedback with `{globals.prefix_short}feedback` if you want changes made!",'done','changelog')
			except:
				if len(''.join(globals.changes))>=1800:
					await emformat.genericmsg(ctx.channel,f"the changelog is too long for discord! either [view the changelog online]({globals.apiurl}changes.html) or check back later when it's been shortened.",'error','changelog')
					if globals.feedbackchannel: await self.bot.get_channel(globals.feedbackchannel).send("<@!140297042709708800>, the changelog is too long! ("+str(len('\n'.join(globals.changes)))+")")
	@changelog.command(name='add')
	async def changelogadd(self,ctx,*,text=None):
		"""Add an entry to the changelog"""
		print('changelog add command')
		if ctx.author.id in globals.superusers:
			if text:
				globals.changes.extend(['\n'+t for t in '\n'.split(text)])
				globals.save()
				await ctx.send("Appended to the changelog successfully!")
		else:
			await emformat.genericmsg(ctx.channel,"this command is restricted.","error","changelog")
	
	@commands.command(no_pm=True)
	async def ownerintrotest(self, ctx):
		await self.send_ownerintro(ctx.guild)
	async def send_ownerintro(self, server):
		em=discord.Embed(title="introducing "+globals.name,type='rich',
		description="hello! i was just added to your server! type `{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short} help` for a list of general commands, but as the owner of *"+server.name+"*, you have more commands available to you;",
		color=discord.Colour(0x2C5ECA),url=globals.apiurl+'#/serverowner')
		em.add_field(name='Automated Messages', inline=False, value=f"*{globals.prefix_short}welcome* - shows a custom welcome message to new members\n*{globals.prefix_short}farewell* - shows a custom announcement whenever a member leaves")
		em.add_field(name='Cleaning', inline=False, value=f"*{globals.prefix_short}janitor* - auto-deletes either bot spam or all messages in a channel after 30 seconds\n*{globals.prefix_short}clean* - cleans a channel of bot spam or all messages for as long as you specify\n*{globals.prefix_short}purge* - erases a section of messages within a channel")
		em.add_field(name='Moderation', inline=False, value=f"*{globals.prefix_short}blacklist* and *{globals.prefix_short}whitelist* - control which words can be used in {globals.name} commands (like echo, image or google search) when in a SFW channel\n*{globals.prefix_short}lockout* - ban users from using {globals.name} if they're abusing it.")
		em.add_field(name='Support', inline=False, value=f"*{globals.prefix_short}changes* - lists all the recent changes to {globals.name}, if you're curious\n*{globals.prefix_short}feedback* - provide feedback directly to the developers if there's a feature or issue you'd like to discuss.")
		em.add_field(name='Need help using these commands?', inline=False, value=f"here's some useful documentation; {globals.apiurl}#/serverowner")
		em.set_thumbnail(url=globals.emurl+"greet.gif")
		em.set_footer(text=f"{globals.name} v{globals.ver} - created by Yiays#5930", icon_url=globals.iconurl)
		await server.owner.send(embed=em)
	
	@commands.command(no_pm=False)
	async def announceupdate(self,ctx,*,msg=''):
		"""Announces updates to the server owners."""
		print('announcetoserverowner command')
		if ctx.author.id in globals.superusers:
			if len(msg)>3:
				async with ctx.channel.typing():
					sent=[]
					failed=0
					ignored=0
					for s in self.bot.guilds:
						if s.owner.id not in sent and s.owner.id not in globals.owneroptout:
							try:
								await emformat.genericmsg(s.owner,f"*hey there, server owner, {globals.name}'s just been updated so here's a list of recent changes...*\n\n{msg}",'done','changelog')
								await s.owner.send("for more information, please visit "+globals.apiurl+"#/serverowner .\n\n"+\
									f"*note: remember to use `{globals.prefix_long+' ' if globals.prefix_long else globals.prefix_short}feedback` to provide feedback.*\n\nif you don't want to recieve these messages, please type `{globals.prefix_short}owneroptout`.")
								sent.append(s.owner.id)
							except:
								failed+=1
						else:
							ignored+=1
					
					await ctx.send('sent patch notes to '+str(len(sent))+' server owners successfully! `'+str(failed)+' failed, '+str(ignored)+' ignored.`')
			else:
				await ctx.send('patch notes are required!')
		else:
			await emformat.genericmsg(ctx.channel,"this command is **super** restricted.","error","announcetoserverowner")
	
	@commands.command(no_pm=False)
	async def owneroptout(self,ctx):
		"""Allows server owners to unsubscribe from all update news."""
		print('owneroptout command')
		if ctx.author.id in [s.owner.id for s in self.bot.guilds]:
			if ctx.author.id not in globals.owneroptout:
				globals.owneroptout.append(ctx.author.id)
				globals.save()
				msg = await ctx.send('done! you will no longer get server owner-related PMs. if you wish to undo this, you will need to PM Yiays#5930')
				await msg.pin()
			else:
				await ctx.send("you've already opted out!")
		else:
			await ctx.send('you don\'t appear to be a server owner!')
