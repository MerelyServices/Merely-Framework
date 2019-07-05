import globals
import asyncio
import discord
from discord.ext import commands
import mysql.connector
import aiohttp
import re

def typeconverter(type):
	if type.startswith('image'):
		if type.startswith('image/gif'):
			return 'gif'
		return 'image'
	if type.startswith('video'):
		return 'video' # could be a silent video, can't tell from here
	if type.startswith('audio'):
		return 'audio'
	if type.startswith('text/html'):
		return 'url'
	return None

def FindURLs(string):
		urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string)
		return urls

class Meme(commands.Cog):
	"""In beta; a new database for automatically storing and indexing memes to make them easier to find"""
	def __init__(self, bot):
		self.bot = bot
		self.session = aiohttp.ClientSession()
	def __delete__(self,instance):
		self.session.close()

	async def BackgroundService(self,skip=0):
		
		for channel in sum(globals.memechannels.values(),[])[skip:]:
			counter = 0
			channel=self.bot.get_channel(channel)
			print('BS: iterating upon #'+channel.name+'...')
			async for message in channel.history(limit=10000):
				counter+=1
				if counter%100 == 0:
					print('BS: '+str(counter))
				await self.ReactionCrawler(message,channel)
	
	async def ReactionCrawler(self,message,channel):
		result = None
		up = []
		down = []
		for reaction in message.reactions:
			if '🔼' in str(reaction.emoji):
				if not reaction.me:
					result = await self.GetMessageUrl(message) if result == None else result
					if result:
						await message.add_reaction('🔼')
				async for user in reaction.users():
					if not user.bot:
						up.append(user.id)
			elif '🔽' in str(reaction.emoji):
				if not reaction.me:
					result = await self.GetMessageUrl(message) if result == None else result
					if result:
						await message.add_reaction('🔽')
				async for user in reaction.users():
					if not user.bot:
						down.append(user.id)
		if down or up:
			if len(up)>=1:
				result = await self.GetMessageUrl(message) if result == None else result
				if result:
					mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password='UChsRQ6scfI0cwGJ',database='meme')
					cursor = mydb.cursor()
					cursor.execute(f"CALL AddMeme({message.id},'{result[1]}',{result[2]},'{result[0]}',@MID);")
					mydb.commit()
					values=');CALL AddMemeVote('.join(["@MID,'"+str(voter)+"',"+'1' if voter in up else '-1' for voter in list(dict.fromkeys(up+down))])
					cursor.execute(f"CALL AddMemeVote({values});",multi=True)
					mydb.commit()
					edge = 4
					for k,v in globals.memechannels.items():
						if channel.id in v: edge = k
					cursor.execute(f"CALL AddEdge(@MID,{self.bot.user.id},{edge});")
					mydb.commit()
					mydb.close()
				else:
					print("Unable to add a meme to the database! ("+str(message.id)+")")
		else:
			result = await self.GetMessageUrl(message) if result == None else result
			if result and len(message.reactions)<=18:
				await message.add_reaction('🔼')
				await message.add_reaction('🔽')
	
	async def GetMessageUrl(self,message):
		urls = FindURLs(message.content)+[a.url for a in message.attachments]
		if urls:
			for url in urls:
				try:
					async with self.session.head(url) as clientresponse:
						if 'content-type' in clientresponse.headers:
							type = clientresponse.headers['content-type'].split(' ')[0]
							if typeconverter(type):
								return (url,typeconverter(type),0 if len(urls)==1 else 1)
						else:
							return None
				except:
					return None
		else: return None

	async def OnMemePosted(self,message):
		result = await self.GetMessageUrl(message)
		if result:
			await message.add_reaction('🔼')
			await message.add_reaction('🔽')
			return 'found type '+result[1]+' at '+result[0]
		return "couldn't find a meme!"
	
	async def OnReaction(self,message_id,channel_id):
		channel = self.bot.get_channel(channel_id)
		message = await channel.fetch_message(message_id)
		await self.ReactionCrawler(message,channel)
	
	@commands.command(pass_context=True, no_pm=True)
	async def memedbtest(self, ctx):
		await ctx.channel.send(await self.OnMemePosted(ctx.message))
	
	@commands.command(pass_context=True, no_pm=False)
	async def memedbscan(self,ctx,skip='0'):
		await ctx.channel.send('Starting message history scan for unreacted memes and reactions...')
		if skip.isdigit(): skip = int(skip)
		else: skip = 0
		try:
			await self.BackgroundService(skip)
		except Exception as e:
			await ctx.channel.send('Failed to complete service: ```py\n'+str(e)+'```')
		else:
			await ctx.channel.send('Background service ended.')
		
	




