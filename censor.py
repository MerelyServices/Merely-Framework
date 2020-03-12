import globals
import asyncio
import discord
import random, re
import aiohttp
from urllib import parse
from difflib import get_close_matches
from pprint import pprint
from discord.ext import commands
import emformat
import help

globals.commandlist['censor']=['blacklist','whitelist','censor']

def sass():
	return random.choice(["keep that in an nsfw channel, filthy weeb.","merely has *standards*","degenerates.","I'm not just gonna let you post filth in a sfw channel.",
												"you people disgust me","merely found a naughty word in this one.","saving the mods from a second of wasted time.","no thank you."])

class Xlist():
	def __init__(self, guild=None):
		self.file = None
		self.guildfile = None
		self.guild = guild
	
	def get(self, onlymain=False):
		""" Generic get method for blacklists/whitelists - if configured as a guildlist, it returns the blacklist with guild modifications. """
		result = []
		try:
			with open(self.file,'r',encoding='utf-8') as f:
				result += f.read().splitlines()
		except FileNotFoundError:
			pass
		
		if self.guild and onlymain == False:
			try:
				with open(self.guildfile,'r',encoding='utf-8') as f:
					for line in f.read().splitlines():
						if line[0] == '+': result.append(line[1:])
						if line[0] == '-': 
							try: result.remove(line[1:])
							except ValueError: print("Failed to remove "+line+" from GuildBlacklist(id="+str(self.guild)+").")
			except FileNotFoundError:
				pass
		
		return result
	
	def add(self, word):
		""" Generic add method for blacklists/whitelists - if configured as a guildlist, it looks for contradictions in the guild list, removes them, and then adds the word locally. """
		if not self.guild:
			with open(self.file,'a',encoding='utf-8') as f:
				f.writeline(word + "\n")
			return True
		else:
			permanent = self.get(onlymain=True)
			keep = []
			try:
				with open(self.guildfile,'r',encoding='utf-8') as f:
					for line in f.read().splitlines():
						if line != '-'+word:
							keep.append(line+'\n')
			except FileNotFoundError:
				pass
			if word not in permanent:
				keep.append('+'+word+'\n')
			with open(self.guildfile,'w',encoding='utf-8') as f:
				f.writelines(keep)
	
	def remove(self, word):
		""" Generic remove method for blacklists/whitelists - if configured as a guild, it looks for contradictions in the guild list, removes them, and then removes the word locally. """
		keep = []
		if not self.guild:
			try:
				with open(self.file,'r',encoding='utf-8') as f:
					for line in f.read().splitlines():
						if word != line:
							keep.append(line+'\n')
			except FileNotFoundError:
				pass
			with open(self.file,'w',encoding='utf-8') as f:
				f.writelines(keep)
			return True
		else:
			permanent = self.get(onlymain=True)
			try:
				with open(self.guildfile,'r',encoding='utf-8') as f:
					for line in f.read().splitlines():
						if line != '+'+word:
							keep.append(line+'\n')
			except FileNotFoundError:
				pass
			if word in permanent:
				keep.append('-'+word+'\n')
			with open(self.guildfile,'w',encoding='utf-8') as f:
				f.writelines(keep)
			return True

class Whitelist(Xlist):
	def __init__(self, guild=None):
		super().__init__(guild)
		self.file = globals.store + 'whitelist.txt'
		if guild:
			self.guildfile = f"{globals.store}whitelist.{guild}.txt"

class Blacklist(Xlist):
	def __init__(self, guild=None):
		super().__init__(guild)
		self.file = globals.store + 'blacklist.txt'
		if guild:
			self.guildfile = f"{globals.store}blacklist.{guild}.txt"
	
	def remove(self, word):
		""" Remove method for blacklists - removes all matches in the blacklist, not just exact matches. """
		keep = []
		remove = globals.dangerous(word, guild=self.guild)
		if remove:
			if not self.guild:
				try:
					with open(self.file,'r',encoding='utf-8') as f:
						for line in f.read().splitlines():
							if line not in remove:
								keep.append(line+'\n')
				except FileNotFoundError:
					pass
				with open(self.file,'w',encoding='utf-8') as f:
					f.writelines(keep)
				return remove
			else:
				permanent = self.get(onlymain=True)
				try:
					with open(self.guildfile,'r',encoding='utf-8') as f:
						for line in f.read().splitlines():
							if line not in ['+'+i for i in remove]:
								keep.append(line+'\n')
				except FileNotFoundError:
					pass
				for rword in remove:
					if rword in permanent:
						keep.append('-'+rword+'\n')
				with open(self.guildfile,'w',encoding='utf-8') as f:
					f.writelines(keep)
				return remove
		return []

class Censor(commands.Cog):
	"""Censor related commands."""
	def __init__(self, bot):
		self.bot = bot
		self.blacklist = {i:Blacklist(i) for i in [0]+[g.id for g in self.bot.guilds]}
		self.whitelist = {i:Whitelist(i) for i in [0]+[g.id for g in self.bot.guilds]}
		globals.dangerous = self.dangerous
	
	async def send_list(self, wordlist, intro, channel):
		introdone = False
		iterations = 0
		while len(wordlist)>0 and iterations < 5:
			if len(wordlist)>1900:
				end = 1900
				while wordlist[end]!=' ': end -= 1
				send = wordlist[:end]
				wordlist = wordlist[end+1:]
			else:
				send = wordlist
				wordlist = ''
			if not introdone:
				send = intro + " ```"+send+"```"
				introdone = True
			else:
				send = "```"+send+"```"
			await channel.send(send)
			iterations += 1
		if iterations == 5:
			await channel.send("there's even more, but I don't want to spam this channel anymore.")
	
	def dangerous(self, text, train=0, guild=0):
		blacklist=self.blacklist[guild].get()
		whitelist=self.whitelist[guild].get()
		matches=[]
		rootwords=text.lower().replace('\n',' ').split(' ')
		if train==0: words=rootwords+[x+y for x,y in zip(rootwords[0::2],rootwords[1::2])]+[x+y for x,y in zip(rootwords[1::2],rootwords[2::2])]
		else: words=rootwords
		alphanum=re.compile(r'[\W]')
		for word in words:
			word=alphanum.sub('',word)
			if word not in whitelist:
				match=get_close_matches(word,blacklist,1,0.75)
				if match:
					if train==1: #whitelist
						matches+=word+" -> "+', '.join(match)+'\n'
						globals.modules['censor'].whitelist[guild].add(word)
						whitelist.append(word)
					elif train==2: #blacklist, if the word was detected
						if word not in blacklist: #only add if it's not a direct match.
							matches+=word
							globals.modules['censor'].blacklist[guild].add(word)
							blacklist.append(word)
					else:
						matches+=match
				elif train==2: #blacklist
					matches+=word
					globals.modules['censor'].blacklist[guild].add(word)
					blacklist.append(word)
	
		if matches: pprint(matches)
		return matches

	@commands.command(pass_context=True, no_pm=True, aliases=['blacklist','whitelist'])
	async def xlist(self, ctx, mode=None, *, word=None):
		"""View and manage the blacklist or whitelist."""
		
		black = None
		if ctx.invoked_with.lower() == 'blacklist': black = True
		if ctx.invoked_with.lower() == 'whitelist': black = False
		if black == None: return
		
		if ctx.guild.id not in self.blacklist or ctx.guild.id not in self.whitelist:
			self.blacklist[ctx.guild.id] = Blacklist(ctx.guild.id)
			self.whitelist[ctx.guild.id] = Whitelist(ctx.guild.id)
		blacklist = self.blacklist[ctx.guild.id]
		whitelist = self.whitelist[ctx.guild.id]
		
		words = None
		if word != None:
			if len(' '.split(word)) > 1:
				words = ' '.split(word)
		
		
		if mode!=None:
			if globals.verbose: print(('black' if black else 'white')+'list '+mode+' command')
			
			# security check
			if ctx.message.author.id not in globals.authusers and ctx.message.author.id != ctx.message.guild.owner.id:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","blacklist")
				return
			if word==None:
				await ctx.channel.send(help.dhelp[('black' if black else 'white')+'list'])
				return
			
			if mode == 'add':
				if words!=None:
					await emformat.genericmsg(ctx.message.channel,"please list one word at a time","error",('black' if black else 'white')+"list")
					return
				
				if black: # blacklist add
					if word in blacklist.get():
						await emformat.genericmsg(ctx.message.channel,"this word is already in the blacklist!","error","blacklist")
						return
					if word in whitelist.get():
						await emformat.genericmsg(ctx.message.channel,"this word is in the whitelist - a direct contradiction is not allowed.","error","blacklist")
						return
					
					matches = self.dangerous(word, guild=ctx.guild.id)
					blacklist.add(word)
					if matches:
						await emformat.genericmsg(ctx.message.channel,"*'"+word+"'* was already covered by `"+', '.join(matches)+"`, but is now blacklisted directly!","done","blacklist")
					else:
						await emformat.genericmsg(ctx.message.channel,"*'"+word+"'* is now blacklisted!","done","blacklist")
					return
				
				else: # whitelist add
					if word in whitelist.get():
						await emformat.genericmsg(ctx.message.channel,"this word is already in the whitelist!","error","whitelist")
						return
					if word in blacklist.get():
						await emformat.genericmsg(ctx.message.channel,"this word is already in the blacklist - a direct contradiction is not allowed.","error","whitelist")
						return
					if not self.dangerous(word, guild=ctx.guild.id):
						await emformat.genericmsg(ctx.message.channel,"this word isn't blocked, no need to whitelist it.","error","whitelist")
						return
					
					whitelist.add(word)
					await emformat.genericmsg(ctx.message.channel,"*'"+word+"'* is now whitelisted!","done","whitelist")
					return
				
			elif mode == 'remove':
				if words!=None:
					await emformat.genericmsg(ctx.message.channel,"please list one word at a time","error",('black' if black else 'white')+"list")
					return
				
				if black: # blacklist remove
					matches = blacklist.remove(word)
					if not matches:
						await emformat.genericmsg(ctx.message.channel,"this word isn't in the blacklist!","error","blacklist")
						return
					await emformat.genericmsg(ctx.message.channel,"the word(s) `"+" ".join(matches)+"` have been unbanned!","done","blacklist")
						
				else: # whitelist remove
					if word not in whitelist.get():
						await emformat.genericmsg(ctx.message.channel,"this word isn't in the whitelist!","error","whitelist")
						return
					whitelist.remove(word)
					await emformat.genericmsg(ctx.message.channel,"the word `"+word+"` has been removed from the whitelist!","done","blacklist")
			
			elif mode == 'train':
				ctx.channel.send("this command is currently unavailable. please try again later.")
				
			else:
				await ctx.channel.send(help.dhelp[('black' if black else 'white')+'list'])
				return
		
		else: # print the xlist
			if globals.verbose: print('xlist command')
			wordprint=''
			for word in (blacklist.get() if black else whitelist.get()):
				wordprint+=word+", "
			
			await self.send_list(wordprint,"here's the current list of "+('black' if black else 'white')+"listed words;",ctx.message.channel)

	"""
	@commands.command(pass_context=True, no_pm=False, aliases=['bl'])
	async def blacklist(self, ctx, *, mode=None):
		\"""View and manage the blacklist, which restricts which words users can use in various commands.\"""
		word=None
		if mode!=None and len(mode.split(' '))>1:
			mode=mode.split(' ')
			word=' '.join(mode[1:]) if len(mode)>2 else mode[1]
			mode=mode[0]
		if mode=='add': #adds more words to the blacklist
			if globals.verbose: print('blacklist add command')
			if ctx.message.author.id in globals.authusers or ctx.message.author.id == ctx.message.guild.owner.id:
				if word==None:
					await ctx.message.channel.send(help.dhelp['blacklist'])
					return
				matches=dangerous(word)
				if ' ' in word:
					await emformat.genericmsg(ctx.message.channel,"please list one word at a time, and make sure that each word doesn't have legitimate uses","error","blacklist")
				elif matches:
					if word not in self.get_blacklist():
						with open(globals.store+'blacklist.txt','a',encoding='utf-8') as f:
							f.write(word+"\n")
						await emformat.genericmsg(ctx.message.channel,"*'"+word+"'* was already covered by `"+" ".join(matches)+"`, but now it is blacklisted directly.","done","blacklist")
					else:
						await emformat.genericmsg(ctx.message.channel,"that word is already covered by `"+" ".join(matches)+"`","done","blacklist")
				elif word in self.get_whitelist():
					await emformat.genericmsg(ctx.message.channel,"`"+word+"` is in the whitelist, a direct contradiction is not allowed.","error","blacklist")
				else:
					with open(globals.store+'blacklist.txt','a',encoding='utf-8') as f:
						f.write(word+"\n")
					await emformat.genericmsg(ctx.message.channel,"*'"+word+"'* is now banned!","done","blacklist")
			else:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","blacklist")
		elif mode=='remove': #removes words from the blacklist
			if globals.verbose: print('blacklist remove command')
			if ctx.message.author.id in globals.authusers or ctx.message.author.id == ctx.message.guild.owner.id:
				if word==None:
					await ctx.message.channel.send(help.dhelp['blacklist'])
					return
				matches=dangerous(word)
				if ' ' in word:
					await emformat.genericmsg(ctx.message.channel,"please list one word at a time and make sure it's actually a word on the `m/blacklist`","error","blacklist")
				elif not matches:
					await emformat.genericmsg(ctx.message.channel,"i can't find any matches!","error","blacklist")
				else:
					keep=[]
					for line in self.get_blacklist():
						if line not in matches:
								keep.append(line+"\n")
					with open(globals.store+'blacklist.txt','w',encoding='utf-8') as f:
						f.writelines(keep)
					await emformat.genericmsg(ctx.message.channel,"the word(s) `"+" ".join(matches)+"` have been unbanned!","done","blacklist")
			else:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","blacklist")
		elif mode=='train': #trains the blacklist using badword lists
			if globals.verbose: print('blacklist train command')
			if ctx.message.author.id in globals.superusers:
				if word==None:
					await emformat.genericmsg(ctx.message.channel,"paste either a string of bad words, or a url to a txt file full of bad words.","error","blacklist")
					return
				if word.startswith('http') and ' ' not in word:
					async with ctx.message.channel.typing():
						header={'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'}
						async with aiohttp.ClientSession() as session:
							async with session.get(word,headers=header) as r:
								if r.status == 200:
									text = await r.text()
								else:
									print('blacklist train: error '+str(r.status))
									await emformat.genericmsg(ctx.message.channel,"i couldn't work with the file you gave me; `error "+str(r.status)+"`","error","blacklist")
				else:
					text=word
				result=dangerous(text,2)
				await emformat.genericmsg(ctx.message.channel,"all of these words were blacklisted;\n```"+', '.join(result)+"```","done","blacklist")
			else:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","blacklist")
		else:
			if globals.verbose: print('blacklist command')
			wordprint=''
			for word in self.get_blacklist():
				wordprint+=word+", "
			
			await self.send_list(wordprint,"here's the current list of blacklisted words;",ctx.message.channel)
	
	@commands.command(pass_context=True, no_pm=False, aliases=['wl'])
	async def whitelist(self, ctx, *, mode=None):
		\"""View and manage the whitelist, which allows words past the blacklist.\"""
		word=None
		if mode!=None and len(mode.split(' '))>1:
			mode=mode.split(' ')
			word=' '.join(mode[1:]) if len(mode)>2 else mode[1]
			mode=mode[0]
		if mode=='add': #adds more words to the whitelist
			if globals.verbose: print('whitelist add command')
			if ctx.message.author.id in globals.authusers or ctx.message.author.id == ctx.message.guild.owner.id:
				if word==None:
					await ctx.message.channel.send(help.dhelp['whitelist'])
					return
				#matches=dangerous(word)
				if ' ' in word:
					await emformat.genericmsg(ctx.message.channel,"please list one word at a time, and make sure that each word doesn't have legitimate uses","error","whitelist")
				#elif not matches:
					#await ctx.message.channel.send("that word isn't covered by the blacklist!")
				elif word in self.get_blacklist():
					await emformat.genericmsg(ctx.message.channel,"`"+word+"` is in the blacklist, a direct contradiction is not allowed.","error","whitelist")
				else:
					with open(globals.store+'whitelist.txt','a',encoding='utf-8') as f:
						f.write(word+"\n")
					await emformat.genericmsg(ctx.message.channel,"*'"+word+"'* is no longer banned!","done","whitelist")
			else:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","whitelist")
		elif mode=='remove': #removes words from the whitelist
			if globals.verbose: print('whitelist remove command')
			if ctx.message.author.id in globals.authusers:
				if word==None:
					await ctx.message.channel.send(help.dhelp['whitelist'])
					return
				whitelist=self.get_whitelist()
				if ' ' in word:
					await emformat.genericmsg(ctx.message.channel,"please list one word at a time and make sure it's actually on the `m/whitelist`","error","whitelist")
				elif word not in whitelist:
					await emformat.genericmsg(ctx.message.channel,"this word isn't in the whitelist!","error","whitelist")
				else:
					keep=[]
					for line in whitelist:
						if line.rstrip()!=word:
								keep.append(line+"\n")
					with open(globals.store+'whitelist.txt','w',encoding='utf-8') as f:
						f.writelines(keep)
					await emformat.genericmsg(ctx.message.channel,"the word `"+word+"` is no longer exempt from the blacklist!","done","whitelist")
			else:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","whitelist")
		elif mode=='train': #trains the whitelist using trusted texts
			if globals.verbose: print('whitelist train command')
			if ctx.message.author.id in globals.superusers:
				if word==None:
					await emformat.genericmsg(ctx.message.channel,"paste either a string of safe words, or a url to a txt file full of safe words.","error","whitelist")
					return
				if word.startswith('http') and ' ' not in word:
					async with ctx.message.channel.typing():
						header={'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'}
						async with aiohttp.ClientSession() as session:
							async with session.get(word,headers=header) as r:
								if r.status == 200:
									text = await r.text()
								else:
									print('whitelist train: error '+str(r.status))
									await emformat.genericmsg(ctx.message.channel,"i couldn't work with the file you gave me; `error "+str(r.status)+"`","error","whitelist")
				else:
					text=word
				result=dangerous(text,1)
				await emformat.genericmsg(ctx.message.channel,"all of these words were whitelisted;\n```"+result+"```","done","whitelist")
			else:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","whitelist")
		else:
			if globals.verbose: print('whitelist command')
			wordprint=''
			for word in self.get_whitelist():
				wordprint+=word+", "
			
			await self.send_list(wordprint,"here's the current list of whitelisted words;",ctx.message.channel)
	"""
	@commands.command(pass_context=True, no_pm=False, aliases=['censorg'])
	async def censor(self, ctx, *, text):
		if globals.verbose: print('censor command')
		danger=self.dangerous(text, guild=(ctx.guild.id if ctx.invoked_with.lower() == 'censor' else 0))
		await ctx.message.channel.send(danger)
	