import globals
import utils
import asyncio
import discord
from discord.ext import commands
import mysql.connector
import aiohttp
import urllib.parse
import re

globals.commandlist['meme']=['meme']

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

class Meme(commands.Cog):
	"""In beta; a new database for automatically storing and indexing memes to make them easier to find"""
	def __init__(self, bot):
		self.bot = bot
		self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
		self.usedmemes = []
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
				await self.RecordMeme(result,message,up,down)
				await message.add_reaction('☑')
		else:
			result = await self.GetMessageUrls(message) if result == -1 else result
			if result and len(message.reactions)<=18:
				await message.add_reaction('🔼')
				await message.add_reaction('🔽')
				
				mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=globals.memedbpass,database='meme')
				cursor = mydb.cursor()
				cursor.execute(f"SELECT Id FROM meme WHERE DiscordOrigin = {message.id} AND CollectionParent IS NULL LIMIT 1")
				result = cursor.fetchone()
				cursor.close()
				if not verified and result != None:
					await message.add_reaction('☑')
				elif verified and result == None:
					await verified.remove(self.bot.user)
	
	async def RecordMeme(self,result,message,up=[],down=[]):
		mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=globals.memedbpass,database='meme')
		cursor = mydb.cursor()
		
		# Add meme, in case it doesn't already exist
		first=True
		for meme in result:
			if first:
				first=False
				cursor.execute(f"CALL AddMeme({message.id},'{meme[1]}',NULL,'{meme[0]}',@MID);")
				mydb.commit()
				cursor.execute(f"SELECT @MID;")
			else:
				cursor.execute(f"CALL AddMeme({message.id},'{meme[1]}',(SELECT @MID),'{meme[0]}',@notMID);")
				mydb.commit()
				cursor.execute(f"SELECT @notMID;")
			result = cursor.fetchone()
			if not result is None:
				mid = result[0]
				try:
					await self.session.get("https://cdn.yiays.com/meme/dl.php?singledl="+str(mid))
					await self.session.get("https://cdn.yiays.com/meme/"+str(mid)+".thumb.jpg")
					await self.session.get("https://cdn.yiays.com/meme/"+str(mid)+".mini.jpg")
				except Exception as e:
					print(e)
		
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
		urls = utils.FindURLs(message.content)+[a.url for a in message.attachments]
		if urls:
			memes=[]
			for url in urls:
				trusted = 0
				try:
					for block in globals.memesites['blocked']:
						if block in url:
							trusted = -1
							return
					for trust in globals.memesites['trusted']:
						if trust in url:
							trusted = 1
					if trusted == -1: return
					if trusted == 0:
						if globals.modchannel:
							modchannel = self.bot.get_channel(globals.modchannel)
							await modchannel.send("a new memeurl pattern has been found!\n"+url+"\nshould it be trusted? (yes/no) *note, this regards the domain name as a whole, not the individual meme.*")
							try:
								msg = await self.bot.wait_for('message', check = lambda m: m.channel == modchannel and m.content in ['yes','no'], timeout=3600.0)
							except asyncio.TimeoutError:
								await modchannel.send('no response detected, ignoring memeurl and moving on...')
								return
							form = 'trusted' if msg.content=='yes' else 'blocked'
							
							await modchannel.send('alright, '+msg.author.mention+' please reply with the most significant part of the url that should be '+form+'; *(for example, `youtube.com/watch?`), type cancel to cancel.*')
							try:
								msg = await self.bot.wait_for('message', check = lambda m: m.channel == modchannel and m.author == msg.author, timeout=300)
							except asyncio.TimeoutError:
								await modchannel.send('no response detected, ignoring memeurl and moving on...')
								return
							if msg.content == 'cancel':
								return
							globals.memesites[form].append(msg.content)
							globals.save()
							await modchannel.send('done! `'+msg.content+'` is now a '+form+' url format!')
								
						else:
							print("[WARN] skipped unknown memeurl because modchannel isn't set!")
							return
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
	
	async def get_meme(self, channel, id=None, search=None):
		mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=globals.memedbpass,database='meme')
		
		if id is None and search is None:
			query = \
			"""
				SELECT Id,Url,Type
				FROM (meme AS r1 LEFT JOIN edge ON Id = edge.memeId)
				JOIN (SELECT CEIL(RAND() * (SELECT MAX(Id) FROM meme)) AS maxId) AS r2
				WHERE r1.Id >= r2.maxId
				HAVING IFNULL(AVG(edge.Rating),4)<=1.5
				ORDER BY r1.Id ASC
				LIMIT 1
			"""
		elif search is not None:
			query = \
			f"""
				SELECT meme.Id,Url,Type,
				(SELECT COALESCE(SUM(memevote.Value),0) FROM memevote WHERE memeId=meme.Id) AS Votes,
				REPLACE(
					REPLACE(
						REPLACE(
							LOWER(
								CONCAT_WS('',
									(SELECT GROUP_CONCAT(Text SEPARATOR '') FROM description WHERE memeId=meme.Id),
									(SELECT GROUP_CONCAT(Name SEPARATOR '') FROM category JOIN categoryvote ON Id=categoryId WHERE memeId=meme.Id),
									(SELECT GROUP_CONCAT(Name SEPARATOR '') FROM tag JOIN tagvote ON Id=tagId WHERE memeId=meme.Id),
									(SELECT GROUP_CONCAT(Text SEPARATOR '') FROM transcription WHERE memeId=meme.Id),
									Type,
									(SELECT IF((SELECT COUNT(*) FROM meme child WHERE CollectionParent = meme.Id)>0,'collection',''))
								)
							)
						,' ','')
					,CHAR(10 using utf8),'')
				,'<br/>','') AS SearchData
				FROM (((((((meme
						LEFT JOIN description ON meme.Id = description.memeId)
						LEFT JOIN transcription ON meme.Id = transcription.memeId)
						LEFT JOIN categoryvote ON categoryvote.memeId = meme.Id)
						LEFT JOIN category ON categoryvote.categoryId = category.Id)
						LEFT JOIN tagvote ON tagvote.tagId = meme.Id)
						LEFT JOIN tag ON tagvote.tagId = tag.Id)
						LEFT JOIN edge ON meme.Id = edge.memeId)
				GROUP BY meme.Id
				HAVING IFNULL(AVG(edge.Rating),4)<=1.5 AND SearchData LIKE "%{mydb.converter.escape(search.lower().replace(' ',''))}%"
				ORDER BY meme.Id DESC
				LIMIT 20;
			"""
		elif id.isdigit():
			query = \
			f"""
				SELECT Id,Url,Type
				FROM meme LEFT JOIN edge ON meme.Id = edge.memeId
				WHERE Id = {id}
				HAVING IFNULL(AVG(edge.Rating),4)<=1.5
				LIMIT 1
			"""
		else:
			print(f'get_meme(self, channel={channel}, id={id}, search={search}) is invalid.')
		
		cursor = mydb.cursor()
		cursor.execute(query)
		row = cursor.fetchone()
		
		if row:
			# shuffle random memes, don't show used memes again
			if id is None and search is None:
				while row[0] in self.usedmemes:
					row = cursor.fetchone()
					if not row:
						cursor.execute(query)
						row = cursor.fetchone()
						if not row:
							break
				self.usedmemes.append(row[0])
				if len(self.usedmemes)>200:
					self.usedmemes.pop(0)
			
			# don't show used search results again
			elif search is not None:
				for _ in range(20):
					if row[0] in self.usedmemes:
						row = cursor.fetchone()
						if row[0] not in self.usedmemes:
							self.usedmemes.append(row[0])
							if len(self.usedmemes)>200:
								self.usedmemes.pop(0)
							break
						if not row:
							break
					else:
						self.usedmemes.append(row[0])
						if len(self.usedmemes)>200:
							self.usedmemes.pop(0)
						break
						
			
			# add id meme to used memes, but don't block it
			elif id is not None:
				self.usedmemes.append(row[0])
				if len(self.usedmemes)>200:
					self.usedmemes.pop(0)
		
		mydb.close()
		
		embed = discord.Embed(color=discord.Color(0xf9ca24))#,url="https://meme.yiays.com/meme/"+str(row[0]),title="open in MemeDB")
		embed.set_footer(text='powered by MemeDB (meme.yiays.com)',icon_url='https://meme.yiays.com/img/icon.png')
		
		if row:
			extra = "https://meme.yiays.com/meme/"+str(row[0])
			if row[2] in ['image', 'gif']:
				embed.set_image(url=row[1])
			elif row[2] == 'text':
				embed.description = row[1]
			else:
				extra=row[1]+' - view online at https://meme.yiays.com/meme/'+str(row[0])
				embed=None
			
			if search is not None:
				extra += '\nmore results at https://meme.yiays.com/search/?q='+urllib.parse.quote_plus(search, safe='')
				
			await channel.send("#"+str(row[0])+": "+extra, embed=embed)
			return True
		else:
			embed.title = "no results found!"
			embed.description = "either there's nothing here, or you've already seen everything."
			await channel.send("", embed=embed)
			return False

	@commands.command(pass_context=True, no_pm=False, aliases=['memes','mem'])
	async def meme(self, ctx, *, n='1'):
		if n.isdigit():
			if globals.verbose: print('meme n command')
			n = min(int(n),10)
			for _ in range(n):
				if not await self.get_meme(ctx.channel):
					break
				await asyncio.sleep(1)
		
		elif n[0] == '#' and n[1:].isdigit(): # meme by id
			if globals.verbose: print('meme id command')
			await self.get_meme(ctx.channel, id=n[1:])
		
		elif n.startswith('delet'):
			if globals.verbose: print('meme delet command')
			await ctx.channel.send("deleting memes is no longer possible, you can however open the meme in MemeDB and downvote it.")
		
		elif n.startswith('add'):
			if globals.verbose: print('meme add command')
			await ctx.channel.send("memes are no longer added by a command. they must appear on the official discord server ( https://discord.gg/f6TnEJM ) and be upvoted.")
		
		else:
			if globals.verbose: print('meme search command')
			search = n
			searchargs = search.split(' ')
			async with ctx.channel.typing():
				if searchargs[-1].isdigit(): # meme search (query) n
					search = ' '.join(searchargs[:-1])
					n = min(int(searchargs[-1]), 10)
					for _ in range(n):
						if not await self.get_meme(ctx.channel, search=search):
							break
					return
				await self.get_meme(ctx.channel, search=search)

