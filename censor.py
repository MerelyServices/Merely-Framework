import globals
import utils
import asyncio
import discord
import random, re
import time
import aiohttp
from urllib import parse
from difflib import get_close_matches
from pprint import pprint
from discord.ext import commands
import emformat
import help

# ['censor']=['blacklist','whitelist','censor']

class Censor(commands.Cog):
	"""Censor related commands."""
	def __init__(self, bot):
		self.bot = bot
		self.blacklist = {i:Censor.Blacklist(self, i) for i in [0]+[g.id for g in self.bot.guilds]}
		self.whitelist = {i:Censor.Whitelist(self, i) for i in [0]+[g.id for g in self.bot.guilds]}
	
	def sass(self):
		return random.choice(["keep that in an nsfw channel, filthy weeb.",f"{globals.name} has *standards*","degenerates.","I'm not just gonna let you post filth in a sfw channel.",
													"you people disgust me",f"{globals.name} found a naughty word in this one.","saving the mods from a second of wasted time.","no thank you."])

	class Xlist():
		def __init__(self, parent, guild=None):
			self.parent = parent
			self.file = None
			self.guildfile = None
			self.guild = guild
			self.cached = utils.Cached()
			self.cachedguild = utils.Cached()
		
		def get(self, onlymain=False):
			""" Generic get method for blacklists/whitelists - if configured as a guildlist, it returns the xlist with guild modifications. """
			if self.cached.old:
				result = []
				try:
					with open(self.file,'r',encoding='utf-8') as f:
						result += f.read().splitlines()
				except FileNotFoundError:
					pass
				self.cached.data = result
			else:
				result = self.cached.data
			
			if self.guild and onlymain == False:
				if self.cachedguild.old:
					try:
						with open(self.guildfile,'r',encoding='utf-8') as f:
							for line in f.read().splitlines():
								if line[0] == '+': result.append(line[1:])
								if line[0] == '-': 
									try: result.remove(line[1:])
									except ValueError: print("ERROR: Failed to remove "+line+" from Blacklist(id="+str(self.guild)+").")
					except FileNotFoundError:
						pass
				else:
					result = self.cachedguild.data
			
			return result
		
		def add(self, words):
			""" Generic add method for blacklists/whitelists - if configured as a guildlist, it looks for contradictions in the guild list, removes them, and then adds the word locally. """
			if isinstance(words, str):
				words = [words]
			
			if not self.guild:
				with open(self.file,'a',encoding='utf-8') as f:
					for word in words:
						f.writeline(word+'\n')
				self.cached.refresh = True
				return words
			
			else:
				keep = []
				try:
					with open(self.guildfile,'r',encoding='utf-8') as f:
						for line in f.read().splitlines():
							if line not in ['-'+word for word in words]:
								keep.append(line+'\n')
				except FileNotFoundError:
					pass
				permanent = self.get(onlymain=True)
				for word in words:
					if word not in permanent:
						keep.append('+'+word+'\n')
				with open(self.guildfile,'w',encoding='utf-8') as f:
					f.writelines(keep)
				self.cachedguild.refresh = True
				return words
			
			return []
		
		def remove(self, words):
			""" Generic remove method for blacklists/whitelists - if configured as a guild, it looks for contradictions in the guild list, removes them, and then removes the word locally. """
			if isinstance(words, str):
				words = [words]
			keep = []
			
			if not self.guild:
				try:
					with open(self.file,'r',encoding='utf-8') as f:
						for line in f.read().splitlines():
							for word in words:
								if word != line:
									keep.append(line+'\n')
				except FileNotFoundError:
					pass
				else:
					with open(self.file,'w',encoding='utf-8') as f:
						f.writelines(keep)
				self.cached.refresh = True
				return words
			
			else:
				try:
					with open(self.guildfile,'r',encoding='utf-8') as f:
						for line in f.read().splitlines():
							if line not in ['+'+word for word in words]:
								keep.append(line+'\n')
				except FileNotFoundError:
					pass
				permanent = self.get(onlymain=True)
				for word in words:
					if word in permanent:
						keep.append('-'+word)
				with open(self.guildfile,'w',encoding='utf-8') as f:
					f.writelines(keep)
				self.cachedguild.refresh = True
				return words
			
			return []

	class Whitelist(Xlist):
		def __init__(self, parent, guild=None):
			super().__init__(parent, guild)
			self.file = globals.store + 'whitelist.txt'
			if guild:
				self.guildfile = f"{globals.store}whitelist.{guild}.txt"

	class Blacklist(Xlist):
		def __init__(self, parent, guild=None):
			super().__init__(parent, guild)
			self.file = globals.store + 'blacklist.txt'
			if guild:
				self.guildfile = f"{globals.store}blacklist.{guild}.txt"
			self.cacheduber = utils.Cached(threshold=600)
		
		def get(self, onlymain=False, onlyuber=False):
			if not onlyuber: result = super().get(onlymain=onlymain)
			else: result = []
			if self.cacheduber.old:
				try:
					with open(globals.store + 'blacklist.uber.txt','r',encoding='utf-8') as f:
						result += f.read().splitlines()
				except FileNotFoundError:
					pass
			else:
				result += self.cacheduber.data
			return result
		
		def remove(self, words):
			""" Remove method for blacklists - removes all matches in the blacklist, not just exact matches. """
			if isinstance(words, str):
				words = [words]
			
			print('blacklist remove')
			
			remove = []
			for word in words:
				remove.extend(self.parent.dangerous(word, guild=self.guild))
			remove = list(set(remove))
			if remove:
				return super().remove(remove)
			return []
	
	async def send_list(self, wordlist, intro, channel, seporator=' '):
		introdone = False
		iterations = 0
		while len(wordlist)>0 and iterations < 5:
			if len(wordlist)>1900:
				end = 1900
				while wordlist[end]!=seporator: end -= 1
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
	async def xlist(self, ctx, mode=None, *, words=None):
		"""View and manage the blacklist or whitelist."""
		
		black = None
		if ctx.invoked_with.lower() == 'blacklist': black = True
		if ctx.invoked_with.lower() == 'whitelist': black = False
		if black == None: return
		
		if ctx.guild.id not in self.blacklist or ctx.guild.id not in self.whitelist:
			self.blacklist[ctx.guild.id] = Censor.Blacklist(self, ctx.guild.id)
			self.whitelist[ctx.guild.id] = Censor.Whitelist(self, ctx.guild.id)
		blacklist = self.blacklist[ctx.guild.id]
		whitelist = self.whitelist[ctx.guild.id]
		
		if words != None:
			if len(words.split(' ')) > 1:
				words = list(set(words.split(' ')))
			else:
				words = [words]
		
		
		if mode!=None:
			if globals.verbose: print(('black' if black else 'white')+'list '+mode+' command')
			
			# security check
			if ctx.message.author.id not in globals.authusers and ctx.message.author.id != ctx.message.guild.owner.id:
				await emformat.genericmsg(ctx.message.channel,"this command is restricted.","error","blacklist")
				return
			if words==None:
				await ctx.channel.send(help.dhelp[('black' if black else 'white')+'list'])
				return
			
			warnings = []
			
			if mode == 'add':
				if black: # blacklist add
					for word in words:
						if word in blacklist.get():
							warnings.append(f"'{word}' is already in the blacklist!")
							words.remove(word)
							continue
						if word in whitelist.get():
							warnings.append(f"'{word}' is already in the whitelist and contradictions aren't allowed.")
							words.remove(word)
							continue
						danger = self.dangerous(word, guild=ctx.guild.id)
						if danger:
							warnings.append(f"'{word}' was already covered by {', '.join(danger)}, but is now blacklisted directly!")
					
					result = blacklist.add(words) if words else []
				
				else: # whitelist add
					for word in words:
						if word in whitelist.get():
							warnings.append(f"'{word}' is already in the whitelist!")
							words.remove(word)
							continue
						if word in blacklist.get():
							warnings.append(f"'{word}' is already in the blacklist and contradictions aren't allowed.")
							words.remove(word)
							continue
						if not self.dangerous(word, guild=ctx.guild.id):
							warnings.append(f"'{word}' isn't blocked, no need to whitelist it.")
							words.remove(word)
							continue
					
					result = whitelist.add(words) if words else []
				
				if result:
					await emformat.genericmsg(ctx.message.channel,f"{'the words ' if len(result)>1 else ''}*'{', '.join(result)}'* {'is' if len(result)==1 else 'are'} now {'black' if black else 'white'}listed{'!' if len(warnings)==0 else ' with some warnings;```'+chr(10).join(warnings)+'```'}","done",('black' if black else 'white')+"list")
					if len(result)>1 and random.random() < 1/3:
						await ctx.channel.send(f"hint: you shouldn't blacklist multiple words if they have valid uses, to ban two words that are only bad together, remove the space between them. ie. `{globals.prefix_short}blacklist add badword` as opposed to `{globals.prefix_short}blacklist add bad word`.")
				else: await emformat.genericmsg(ctx.message.channel,f"no changes were made! {'these warnings' if len(warnings)>1 else 'this warning'} might explain why...```{chr(10).join(warnings)}```","error",('black' if black else 'white')+"list")
				return
				
			elif mode == 'remove':
				if black: # blacklist remove
					for word in words:
						if word not in blacklist.get():
							warnings.append(f"'{word}' isn't in the blacklist!")
							words.remove(word)
							continue
						if word in blacklist.get(onlyuber=True):
							warnings.append(f"'{word}' cannot be removed from the blacklist: some words just shouldn't be whitelisted.")
							words.remove(word)
							continue
					
					result = blacklist.remove(words) if words else []
						
				else: # whitelist remove
					for word in words:
						if word not in whitelist.get():
							warnings.append(f"'{word}' isn't in the whitelist!")
							words.remove(word)
							continue
					
					result = whitelist.remove(words) if words else []
				
				if result: await emformat.genericmsg(ctx.message.channel,f"{'the words ' if len(result)>1 else ''}*'{', '.join(result)}'* {'is' if len(words)==1 else 'are'} no longer {'black' if black else 'white'}listed{'!' if len(warnings)==0 else ' with some warnings;```'+chr(10).join(warnings)+'```'}","done",('black' if black else 'white')+"list")
				else: await emformat.genericmsg(ctx.message.channel,f"no changes were made! {'these warnings' if len(warnings)>1 else 'this warning'} might explain why...```{chr(10).join(warnings)}```","error",('black' if black else 'white')+"list")
				return
			
			elif mode == 'train':
				training_data = None
				if len(words)==1 and len(utils.FindURLs(words[0]))==1:
					async with ctx.channel.typing():
						async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
							try:
								async with session.get(words[0]) as r:
									if r.status == 200:
										if r.headers['content-type'] == 'text/plain':
											training_data = await r.text()
											training_data = training_data.split()
										else:
											await emformat.genericmsg(ctx.channel,"the file at the provided url isn't a text file! (expected `text/plain`, got `{r.headers['content-type']}`)","error",('black' if black else 'white')+"list")
											return
									else:
										await emformat.genericmsg(ctx.channel,f"downloading the provided url caused an `error {r.status}`...","error",('black' if black else 'white')+"list")
										return
							except Exception as e:
								await ctx.channel.send("failed to download the file!")
								print(e)
				else:
					await ctx.channel.send("this command takes a url to a text file, please provide one (you can upload a text file to this chat and copy the link to it)")
					return
				
				if training_data:
					results = []
					add = []
					async with ctx.channel.typing():
						for word in training_data:
							if black:
								# blacklist train
								if word not in blacklist.get():
									if word in whitelist.get():
										results.append(f" - didn't blacklist {word}: direct contradictions of the whitelist are not allowed.")
										continue
									add.append(word)
							else:
								#whitelist train
								if word not in whitelist.get():
									if word in blacklist.get():
										results.append(f" - didn't whitelist {word}: direct contradictions of the blacklist are not allowed.")
										continue
									if not self.dangerous(word, guild=ctx.guild.id):
										continue
									add.append(word)

						if add:
							if black:
								for word in blacklist.add(add):
									results.append(f" - blacklisted {word}!")

					if results:
						await self.send_list('\n'.join(results), "here's the results of processing the training data...", ctx.channel, seporator='\n')
					else:
						await ctx.channel.send("after processing the training data, no changes were made!")
				else:
					await ctx.channel.send("that text file appears to be empty!")

			else:
				await ctx.channel.send(help.dhelp[('black' if black else 'white')+'list'])
				return
		
		else: # print the xlist
			if globals.verbose: print(('black' if black else 'white')+'list command')
			wordprint=''
			for word in (blacklist.get() if black else whitelist.get()):
				wordprint+=word+", "
			
			await self.send_list(wordprint,"here's the current list of "+('black' if black else 'white')+"listed words;",ctx.message.channel)

	@commands.command(pass_context=True, no_pm=False)
	async def censor(self, ctx, *, text):
		if globals.verbose: print('censor command')
		danger=self.dangerous(text, guild=(ctx.guild.id if ctx.invoked_with.lower() == 'censor' else 0))
		await ctx.message.channel.send(danger)
	