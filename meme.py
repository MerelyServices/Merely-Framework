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
		urls = re.findall(r'(http[s]?:\/\/[A-z0-9/?.&%;:\-=@]+)', string)
		return urls

<<<<<<< Updated upstream
=======
globals.commandlist['meme']=['meme']

>>>>>>> Stashed changes
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
			print("BS: 0",end='\r')
			async for message in channel.history(limit=10000):
				counter+=1
				print('BS: '+str(counter),end='\r')
				await self.ReactionCrawler(message,channel)
		print('BS: done')
	
	async def ReactionCrawler(self,message,channel):
		result = -1
		up = []
		down = []
		verified = False
		for reaction in message.reactions:
			if '🔼' in str(reaction.emoji):
				if not reaction.me:
					result = await self.GetMessageUrls(message) if result == -1 else result
					if result:
						await message.add_reaction('🔼')
				async for user in reaction.users():
					if not user.bot:
						up.append(user.id)
						await reaction.remove(user)
			elif '🔽' in str(reaction.emoji):
				if not reaction.me:
					result = await self.GetMessageUrls(message) if result == -1 else result
					if result:
						await message.add_reaction('🔽')
				async for user in reaction.users():
					if not user.bot:
						down.append(user.id)
						await reaction.remove(user)
			elif '☑' in str(reaction.emoji):
				verified = reaction
		if down or up:
			if len(up)>=1:
				result = await self.GetMessageUrls(message) if result == -1 else result
				self.RecordMeme(result,message,up,down)
				await message.add_reaction('☑')
		else:
			result = await self.GetMessageUrls(message) if result == -1 else result
			if result and len(message.reactions)<=18:
				await message.add_reaction('🔼')
				await message.add_reaction('🔽')
				
				mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=globals.memedbpass,database='meme')
				cursor = mydb.cursor()
				cursor.execute(f"SELECT Id FROM meme WHERE DiscordOrigin = {message.id}")
				result = cursor.fetchone()
				cursor.close()
				if not verified and result != None:
					await message.add_reaction('☑')
				elif verified and result == None:
					await verified.remove(self.bot.user)
	
	def RecordMeme(self,result,message,up=[],down=[]):
		mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=globals.memedbpass,database='meme')
		cursor = mydb.cursor()
		
		# Add meme, in case it doesn't already exist
		first=True
		for meme in result:
			if first:
				first=False
				cursor.execute(f"CALL AddMeme({message.id},'{meme[1]}',NULL,'{meme[0]}',@MID);")
				mydb.commit()
			else:
				cursor.execute(f"CALL AddMeme({message.id},'{meme[1]}',@MID,'{meme[0]}',@notMID);")
		if len(result)>1:
			mydb.commit()
		
		# Add user, in case they don't exist
		for voter in list(dict.fromkeys(up+down)):
			cursor.execute(f"CALL AddUser({str(voter)},NULL,NULL);")
		mydb.commit()
		
		# Add their vote, finally.
		for voter in list(dict.fromkeys(up+down)):
			try:
				cursor.execute(f"CALL AddMemeVote(@MID,'{str(voter)}',{('1' if voter in up else '-1')});")
			except:
				print(cursor.statement)
				raise
		mydb.commit()
		
		# Add an edge rating from the bot based on where it is
		edge = 4
		for k,v in globals.memechannels.items():
			if message.channel.id in v: edge = k
		cursor.execute(f"CALL AddEdge(@MID,{self.bot.user.id},{edge});")
		mydb.commit()
		mydb.close()
	def RemoveVote(self,mid,uid):
		mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=globals.memedbpass,database='meme')
		cursor = mydb.cursor()
		cursor.execute('DELETE FROM memevote WHERE memeId = (SELECT Id FROM meme WHERE DiscordOrigin='+str(mid)+') and userId = '+str(uid)+';')
		mydb.commit()
		mydb.close()
	
	async def GetMessageUrls(self,message):
		urls = FindURLs(message.content)+[a.url for a in message.attachments]
		if urls:
			memes=[]
			for url in urls:
				pass = 0
				try:
<<<<<<< Updated upstream
=======
					for block in globals.memesites['blocked']:
						if block in url:
							pass = -1
							return
					for trust in globals.memesites['trusted']:
						if trust in url:
							pass = 1
					if pass == -1: return
					if pass == 0:
						if globals.modchannel:
							modchannel = self.bot.get_channel(globals.modchannel)
							await modchannel.send("a new memeurl pattern has been found!\n"+url+"\nshould it be trusted? (yes/no) *note, this regards the domain name as a whole, not the individual meme.*")
							try:
								msg = await self.bot.wait_for('message', check=lambda m: return m.channel == modchannel and m.content in ['yes','no'], timeout=3600.0)
							except asyncio.TimeoutError:
								await modchannel.send('no response detected, ignoring memeurl and moving on...')
								return
							form = 'trusted' if msg.content=='yes' else 'blocked'
							
							await modchannel.send('alright, '+msg.author.mention+' please reply with the most significant part of the url that should be '+form+'; *(for example, `youtube.com/watch?`), type cancel to cancel.*')
							try:
								msg = await self.bot.wait_for('message', check=lambda m: return m.channel == modchannel and m.author == msg.author, timeout=300)
							except asyncio.TimeoutError:
								await modchannel.send('no response detected, ignoring memeurl and moving on...')
								return
							if msg.content == 'cancel':
								return
							globals.memesites[form].append(msg.content)
							await modchannel.send('done! `'+msg.content+'` is now a '+form+' url format!')
								
						else:
							print("[WARN] skipped unknown memeurl because modchannel isn't set!")
							return
>>>>>>> Stashed changes
					async with self.session.head(url) as clientresponse:
						if 'content-type' in clientresponse.headers:
							type = clientresponse.headers['content-type'].split(' ')[0]
							if typeconverter(type):
								memes.append([url,typeconverter(type)])
				except:
					continue
			return memes
		else: return None

	async def OnMemePosted(self,message):
		result = await self.GetMessageUrls(message)
		if result:
			await message.add_reaction('🔼')
			await message.add_reaction('🔽')
			out = ''
			for item in result:
				out+='found type '+item[1]+' at '+item[0]+'\n'
			return out
		return "couldn't find a meme!"
	
	async def OnReaction(self,add,message_id,user_id,channel_id=None,emoji=None):
		if add:
			channel = self.bot.get_channel(channel_id)
			message = await channel.fetch_message(message_id)
			await self.ReactionCrawler(message,channel)
		else:
			self.RemoveVote(message_id,user_id)
	
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
		
	




