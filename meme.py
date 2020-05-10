import globals
import utils,emformat
import asyncio
import discord
from discord.ext import commands
import mysql.connector
import time, datetime
import aiohttp
import urllib.parse
import re

# ['meme']=['meme']

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
	def __init__(self, bot, dbpassword):
		self.bot = bot
		self.dbpassword = dbpassword
		self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60))
		self.memes = {}
		self.searches = {}
		self.usedmemes = Meme.UsedMemes(self.memes)
	def __delete__(self,instance):
		self.session.close()
	
	class UsedMemes(list):
		def __init__(self, memepool):
			self.memepool = memepool
		
		def append(self, item):
			super().append(item)
			if len(self) > max(len(self.memepool), 100) / 2:
				self.pop(0)
	
	class DB():
		def __init__(self, dbpassword):
			self.dbpassword = dbpassword
	
	class DBMeme(DB):
		def __init__(self, dbpassword, usedmemes, memepool, id=None):
			super().__init__(dbpassword)
			self.usedmemes = usedmemes
			self.memepool = memepool
			self.id = id
			self.origin = None
			self.true_origin = None,
			self.type = None
			self.collectionparent = None
			self.url = None
			self.originalurl = None
			self.color = 0xF9CA24
			self.date = int(time.time())
			self.hidden = False
			self.edge = 4.0
			self.nsfw = False
			self.categories = {}
			self.tags = {}
			self.descriptions = []
			self.transcriptions = []
			self.in_db = False
			self.status = 200
			
			self.cache_age = int(time.time())
		
		async def post(self, channel, owner=None):
			if self.id in self.usedmemes:
				return False
			
			self.usedmemes.append(self.id)
			
			if self.type in ['audio', 'video', 'webm', 'url']:
				await channel.send(self.url)
			if self.status == 404:
				await emformat.make_embed(channel, message='', title="Not found!", description="Unable to locate this meme, are you sure it exists?", author=None)
				return False
			if self.status == 403:
				await emformat.make_embed(channel, message='', title="Permission denied!", description="To view this meme, login with an administrative account.", author=None, link=f"https://meme.yiays.com/meme/{self.id}" if self.in_db else '')
				return False
			if self.nsfw and not channel.is_nsfw():
				await emformat.make_embed(channel, message='', title="This meme is potentially nsfw!", description="The channel must be marked as nsfw for this meme to be shown.", author=None, link=f"https://meme.yiays.com/meme/{self.id}" if self.in_db else '')
				return False
			await emformat.make_embed(channel,
																message = '',
																title = "Meme" + (f" #{self.id} on MemeDB" if self.in_db else ''),
																description = self.url if self.type == 'text' else self.descriptions[0].text if len(self.descriptions) else f"This meme needs a description. *({globals.prefix_short}meme #{self.id} description)*" if self.in_db else "Upvote this meme to add it to MemeDB!",
																color = self.color,
																author = "Posted by "+owner.mention if owner else None,
																image = self.url if self.type in ['image', 'gif'] else f"https://cdn.yiays.com/meme/{self.id}.thumb.jpg" if type in ['video', 'webm'] else '',
																fields = {
																	"categories": ', '.join([name for name in self.categories.keys()]) if len(self.categories) else "None yet, you should suggest one!",
																	"tags": ', '.join([name for name in self.tags.keys()]) if len(self.tags) else "None yet, you should suggest some!"
																} if self.in_db else {},
																link = f"https://meme.yiays.com/meme/{self.id}" if self.in_db else '')
			
			return True
		
		def fetch(self, id, depth=2):
			query = \
			f"""
				SELECT meme.*, IFNULL(AVG(edge.Rating),4) AS Edge
				FROM meme LEFT JOIN edge ON meme.Id = edge.memeId
				WHERE Id = {id}
				LIMIT 1
			"""
			
			mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=self.dbpassword,database='meme')
			cursor = mydb.cursor(dictionary=True)
			cursor.execute(query)
			row = cursor.fetchone()
			
			mydb.close()
			
			return row
		
		def getrandom(self, depth=2):
			query = \
			"""
				SELECT r1.*, IFNULL(AVG(edge.Rating),4) AS Edge
				FROM (meme AS r1 LEFT JOIN edge ON Id = edge.memeId)
				JOIN (SELECT CEIL(RAND() * (SELECT MAX(Id) FROM meme)) AS maxId) AS r2
				WHERE r1.Id >= r2.maxId
				ORDER BY r1.Id ASC
				LIMIT 1
			"""
			
			mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=self.dbpassword,database='meme')
			cursor = mydb.cursor(dictionary=True)
			cursor.execute(query)
			row = cursor.fetchone()
			
			mydb.close()
			
			return self.getmeme(depth=depth, row=row)
		
		def getmeme(self, id=None, depth=2, row='fetchplz'):
			# depth is still to be implemented
			# depth 0; just the meme
			# depth 1; tags and cats
			# depth 2; tags, cats, desc and trans
			if id is None: id = self.id
			else: self.id = id
			
			if self.in_db and self.cache_age > int(time.time()) - 60*60*24: # < cache lasts 24 hours
				return self
			
			if row == 'fetchplz':
				row = self.fetch(id, depth=depth)
			
			self.status = 404
			if row is not None and row['Id'] is not None:
				self.status = 200
				
				self.id			= row['Id']
				self.origin	= row['DiscordOrigin']
				self.type		= row['Type']
				self.collectionparent = row['CollectionParent']
				self.url		= row['Url']
				self.originalurl = row['OriginalUrl']
				if row['Color'] is not None: self.color	= int('0x' + row['Color'][1:], 16)
				self.date		= row['Date'].timestamp()
				self.hidden = row['Hidden']
				self.edge		= row['Edge']
				self.nsfw 	= row['Nsfw']
				self.in_db	= True
				
				if self.hidden:
					self.status = 403
				
				if self.edge >= 0.5:
					# self.nsfw = True - potentially really annoying
					if self.edge >= 1.5:
						self.status = 403
		
				self.gettags()
				self.getcats()
				self.getdescriptions()
				self.gettranscriptions()
		
				self.cache_age = int(time.time())
		
				self.memepool[self.id] = self
			
			return self
		
		def getdescriptions(self):
			query = \
			f"""
				SELECT description.*
				FROM description
				LEFT JOIN descvote ON description.Id = descvote.descId
				WHERE memeId = {self.id}
				GROUP BY description.Id
				ORDER BY SUM(descvote.Value) DESC
			"""
			
			mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=self.dbpassword,database='meme')
			cursor = mydb.cursor(dictionary=True)
			cursor.execute(query)
			
			self.descriptions = []
			for row in cursor.fetchall():
				self.descriptions.append(Meme.DBDescription(id=row['Id'], author=row['userId'], editid=row['editId'], text=row['Text']))
			
		def gettranscriptions(self):
			query = \
			f"""
				SELECT transcription.*
				FROM transcription
				LEFT JOIN transvote ON transcription.Id = transvote.transId
				WHERE memeId = {self.id}
				GROUP BY transcription.Id
				ORDER BY SUM(transvote.Value) DESC
			"""
			
			mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=self.dbpassword,database='meme')
			cursor = mydb.cursor(dictionary=True)
			cursor.execute(query)
			
			self.transcriptions = []
			for row in cursor.fetchall():
				self.transcriptions.append(Meme.DBTranscription(id=row['Id'], author=row['userId'], editid=row['editId'], text=row['Text']))
			
		
		def gettags(self):
			query = \
			f"""
				SELECT tagvote.userId, tagvote.Value, tag.Id, tag.Name
				FROM tagvote
				LEFT JOIN tag ON tagvote.tagId = tag.Id
				WHERE memeId = {self.id}
			"""
			
			mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=self.dbpassword,database='meme')
			cursor = mydb.cursor(dictionary=True)
			cursor.execute(query)
			
			for row in cursor.fetchall():
				if row['Name'] not in self.tags:
					self.tags[row['Name']] = Meme.DBTag(id=row['Id'], name=row['Name'], voters={})
				self.tags[row['Name']].voters[row['userId']] = row['Value']
			
			mydb.close()
			
			return self.tags
		
		def getcats(self):
			query = \
			f"""
				SELECT categoryvote.userId, categoryvote.Value, category.Id, category.Name
				FROM categoryvote
				LEFT JOIN category ON categoryvote.categoryId = category.Id
				WHERE memeId = {self.id}
			"""
			
			mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=self.dbpassword,database='meme')
			cursor = mydb.cursor(dictionary=True)
			cursor.execute(query)
			
			for row in cursor.fetchall():
				if row['Name'] not in self.categories:
					self.categories[row['Name']] = Meme.DBCategory(id=row['Id'], name=row['Name'], voters={})
				self.categories[row['Name']].voters[row['userId']] = row['Value']
			
			mydb.close()
			
			return self.categories
		
		def savememe(self):
			# TODO
			
			self.savetags()
			self.savecats()
			
			return True
		
		def savetags(self):
			return True
		
		def savecats(self):
			return True
	
	class DBSearch(DB):
		def __init__(self, dbpassword, memepool, usedmemes, query, results=[]):
			super().__init__(dbpassword)
			self.memepool = memepool
			self.usedmemes = usedmemes
			self.query = query
			self.results = results
		
		def fetch(self):
			mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=self.dbpassword,database='meme')
			query = \
			f"""
				SELECT meme.*, IFNULL(AVG(edge.Rating),4) AS Edge,
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
				HAVING SearchData LIKE "%{mydb.converter.escape(self.query.lower().replace(' ',''))}%"
				ORDER BY meme.Id DESC
				LIMIT 20;
			"""
			
			cursor = mydb.cursor(dictionary=True)
			cursor.execute(query)
			
			for row in cursor.fetchall():
				if row['Id'] not in self.memepool:
					self.memepool[row['Id']] = Meme.DBMeme(dbpassword=self.dbpassword, usedmemes=self.usedmemes, memepool=self.memepool)
				self.memepool[row['Id']].getmeme(id=row['Id'], row=row)
				self.results.append(self.memepool[row['Id']])
			
			mydb.close()
			
			return self.results
		
		def pick(self):
			for result in self.results:
				if result.id not in self.usedmemes:
					return result
			return None
		
		async def post(self, channel, n=1):
			i = 0
			while i < int(n):
				meme = self.pick()
				if meme is None:
					return
				success = await meme.post(channel)
				if success:
					i += 1
				await asyncio.sleep(1)
	
	class DBTag():
		def __init__(self, id=None, name="", voters={}):
			self.id = id
			self.name = name
			self.voters = voters
	
	class DBCategory():
		def __init__(self, id=None, name="", voters={}):
			self.id = id
			self.name = name
			self.voters = voters
	
	class DBDescription():
		def __init__(self, id=None, author=None, editid=None, text=""):
			self.id = id
			self.author = author
			self.editid = editid
			self.text = text
		
		def __str__(self):
			return self.text
	
	class DBTranscription():
		def __init__(self, id=None, author=None, editid=None, text=""):
			self.id = id
			self.author = author
			self.editid = editid
			self.text = text
		
		def __str__(self):
			return self.text
		
	
	async def BackgroundService(self,skip=0):
		
		for channel in [m.id for m in globals.memechannels][skip:]:
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
				
				mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=self.dbpassword,database='meme')
				cursor = mydb.cursor()
				cursor.execute(f"SELECT Id FROM meme WHERE DiscordOrigin = {message.id} AND CollectionParent IS NULL LIMIT 1")
				result = cursor.fetchone()
				cursor.close()
				if not verified and result != None:
					await message.add_reaction('☑')
				elif verified and result == None:
					await verified.remove(self.bot.user)
	
	async def RecordMeme(self,result,message,up=[],down=[]):
		mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=self.dbpassword,database='meme')
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
				cursor.execute(f"CALL AddUser({voter},NULL,NULL);")
				mydb.commit()
			
			# Add their vote, finally.
			for voter in list(dict.fromkeys(up+down)):
				cursor.execute(f"CALL AddMemeVote({mid},'{voter}',{('1' if voter in up else '-1')});")
				mydb.commit()
			
			# Add an edge rating from the bot based on where it is
			edge = 4
			tags = []
			cats = []
			for memechannel in globals.memechannels:
				if message.channel.id == memechannel.id:
					edge = memechannel.edge
					tags = memechannel.tags
					cats = memechannel.categories
			cursor.execute(f"CALL AddEdge({mid},{self.bot.user.id},{edge});")
			mydb.commit()
			if tags:
				inserts = []
				for tag in tags:
					if len(tag)>0: inserts.append(f"({tag}, {self.bot.user.id}, {mid}, 1)")
				if len(inserts)>0:
					inserts = ','.join(inserts)
					cursor.execute(f"INSERT IGNORE INTO tagvote(tagId, userId, memeId, Value) VALUES{inserts}")
					mydb.commit()
			if cats:
				inserts = []
				for cat in cats:
					if len(cat)>0: inserts.append(f"({cat}, {self.bot.user.id}, {mid}, 1)")
				if len(inserts)>0:
					inserts = ','.join(inserts)
					cursor.execute(f"INSERT IGNORE INTO categoryvote(categoryId, userId, memeId, Value) VALUES{inserts}")
					mydb.commit()
		
		mydb.close()
	
	def RemoveVote(self,mid,uid):
		mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=self.dbpassword,database='meme')
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

	@commands.command(pass_context=True, no_pm=False, aliases=['memes','mem'])
	async def meme(self, ctx, *, n='1'):
		if n.isdigit():
			if globals.verbose: print('meme n command')
			i = 0
			while i < int(n):
				meme = Meme.DBMeme(dbpassword=self.dbpassword, usedmemes=self.usedmemes, memepool=self.memes).getrandom()
				self.memes[meme.id] = meme
				success = await meme.post(ctx.channel)
				if success:
					i += 1
				await asyncio.sleep(1)
		
		elif n[0] == '#' and n[1:].isdigit(): # meme by id
			if globals.verbose: print('meme id command')
			id=n[1:]
			if id not in self.memes.keys():
				meme = Meme.DBMeme(dbpassword=self.dbpassword, usedmemes=self.usedmemes, memepool=self.memes, id=id)
			else:
				meme = memes[id]
			meme.getmeme()
			await meme.post(ctx.channel)
		
		elif n == 'delet':
			if globals.verbose: print('meme delet command')
			await ctx.channel.send("deleting memes is no longer possible, you can, however, downvote it.")
		
		elif n == 'add':
			if globals.verbose: print('meme add command')
			await ctx.channel.send("memes are no longer added by a command. they must be added using a designated channel and upvoted.")
		
		else:
			if globals.verbose: print('meme search command')
			search = n
			n = 1
			searchargs = search.split(' ')
			async with ctx.channel.typing():
				if searchargs[-1].isdigit(): # meme search (query) n
					search = ' '.join(searchargs[:-1])
					n = min(int(searchargs[-1]), 10)
				
				searcher = Meme.DBSearch(dbpassword=self.dbpassword, memepool=self.memes, usedmemes=self.usedmemes, query=search)
				searcher.fetch()
				await searcher.post(ctx.channel, n=n)

