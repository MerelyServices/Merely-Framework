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

globals.commandlist['censor']=['blacklist','whitelist']

def dangerous(text,train=0):
	blacklist=Censor.get_blacklist(globals.modules['censor'])
	whitelist=Censor.get_whitelist(globals.modules['censor'])
	matches=[]
	rootwords=text.lower().replace('\n',' ').split(' ')
	if train==0: words=rootwords+[x+y for x,y in zip(rootwords[0::2],rootwords[1::2])]+[x+y for x,y in zip(rootwords[1::2],rootwords[2::2])]
	else: words=rootwords
	#pprint(words)
	alphanum=re.compile(r'[\W]')
	for word in words:
		word=alphanum.sub('',word)
		if word not in whitelist:
			match=get_close_matches(word,blacklist,1,0.75)
			if match:
				if train==1: #whitelist
					matches+=word+" -> "+', '.join(match)+'\n'
					with open(globals.store+'whitelist.txt','a',encoding='utf-8') as f:
						f.write(word+"\n")
					whitelist.append(word)
				elif train==2: #blacklist, if the word was detected
					if word not in blacklist: #only add if it's not a direct match.
						matches+=word
						with open(globals.store+'blacklist.txt','a',encoding='utf-8') as f:
							f.write(word+"\n")
						blacklist.append(word)
				else:
					matches+=match
			elif train==2: #blacklist
				matches+=word
				with open(globals.store+'blacklist.txt','a',encoding='utf-8') as f:
					f.write(word+"\n")
				blacklist.append(word)
				
	if matches: pprint(matches)
	return matches

def sass(name):
	return random.choice(["i can't search for *that*!","*gasp* you perv!","i don't want that in my browser history.","*what would u're mom say?*",
												"this isn't a game "+name+".","get Zo to do your dirty work, not me!","that isn't going to happen anytime soon...",
												"*gasp* "+name+" has some weird fetishes...","i wasn't made for that!","i'm not gonna search for that outside of a nsfw channel..."])

class Censor(commands.Cog):
	"""Censor related commands."""
	def __init__(self, bot):
		self.bot = bot
	
	def get_blacklist(self):
		with open(globals.store+'blacklist.txt','r',encoding='utf-8') as f:
			return f.read().splitlines()
	
	def get_whitelist(self):
		with open(globals.store+'whitelist.txt','r',encoding='utf-8') as f:
			return f.read().splitlines()

	@commands.command(pass_context=True, no_pm=False, aliases=['bl'])
	async def blacklist(self, ctx, *, mode=None):
		"""View and manage the blacklist, which restricts which words users can use in various commands."""
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
			await ctx.message.channel.send("here's the current list of blacklisted words;```"+wordprint[:1900]+"```")
			if len(wordprint)>1900: await ctx.message.channel.send("```"+wordprint[1900:3800]+"```")
			if len(wordprint)>3800: await ctx.message.channel.send("the blacklist is too long!")
	
	@commands.command(pass_context=True, no_pm=False, aliases=['wl'])
	async def whitelist(self, ctx, *, mode=None):
		"""View and manage the whitelist, which allows words past the blacklist."""
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
				matches=dangerous(word)
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
			await ctx.message.channel.send("here's the current list of whitelisted words;```"+wordprint+"```")
	
	@commands.command(pass_context=True, no_pm=False)
	async def censor(self, ctx, *, text):
		if globals.verbose: print('censor command')
		danger=dangerous(text)
		await ctx.message.channel.send(danger)
	