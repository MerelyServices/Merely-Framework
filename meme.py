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
import random

# ['meme']=['meme','memedbscan','memedbtest']

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

class DudMeme():
	"""Dud version of Meme class for passing through to DB* elements"""
	def __init__(self):
		dbpassword = ""
		searches = {}
		usedmemes = {}
		users = {}
		memes = {}
		tags = {}
		categories = {}

class Meme(commands.Cog):
	"""Database and API for collecting, organizing and presenting memes"""
	def __init__(self, bot, dbpassword):
		self.bot = bot
		self.backgroundservice = None
		self.dbpassword = dbpassword
		self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60))
		self.searches = {}
		self.usedmemes = {g.id:Meme.UsedMemes(self) for g in self.bot.guilds} #TODO: Stop this from crashing
		self.users = {}
		
		if globals.verbose: print("filling meme/tags/categories cache...")
		self.memes = {}
		Meme.DBMeme(self).fetchall() # <- this takes 5 seconds on the main thread (after memedb caches the first query), probably can't be optimized much, but makes all searches instant
		self.tags = {}
		Meme.DBTag(self).fetchall()
		self.categories = {}
		Meme.DBCategory(self).fetchall()
		if globals.verbose: print("meme/tags/categories cache done!")
		
		self.bot.events['on_ready'].append(self.BackgroundService)
		self.bot.events['on_message'].append(self.on_message)
		self.bot.events['on_raw_reaction_add'].append(self.on_raw_reaction_add)
		self.bot.events['on_raw_reaction_remove'].append(self.on_raw_reaction_remove)
	
	def __del__(self):
		pass
		#TODO: make this work...
		# await self.session.close()
	
	class UsedMemes(list):
		def __init__(self, parent):
			self.parent = parent
		
		def append(self, item):
			super().append(item)
			if len(self) > max(len(self.parent.memes), 100) / 2:
				self.pop(0)
	
	class DB():
		def __init__(self, dbpassword):
			self.dbpassword = dbpassword
			self.connection = None
			self.cache_age = 0
		
		def connect(self):
			self.connection = mysql.connector.connect(host='192.168.1.120',user='meme',password=self.dbpassword,database='meme')
		
		def disconnect(self):
			self.connection.close()
		
		def selectquery(self, selects:list, _from:str, joins=[], wheres=[], groups=[], havings=[], orders=[], limit="") -> str:
			query = []
			
			query.append(f"SELECT {','.join(selects)}")
			
			if len(joins)>0:
				query.append(f"FROM {'('*len(joins) + _from}")
				for join in joins: query.append(f"{join})")
			else:
				query.append(f"FROM {_from}")
			
			if len(wheres)>0:
				query.append(f"WHERE {' AND '.join(wheres)}")
			
			if len(groups)>0:
				query.append(f"GROUP BY {','.join(groups)}")
			
			if len(havings)>0:
				query.append(f"HAVING {' AND '.join(havings)}")
			
			if len(orders)>0:
				query.append(f"ORDER BY {','.join(orders)}")
			
			if len(limit)>0:
				query.append(f"LIMIT {limit};")
			
			return ' '.join(query)
		
		def runquery(self, query, fetchmode, dictionary=True):
			""" fetchmode 0: fetches nothing, 1: fetches one, 2: fetches all """
			if self.connection is None or not self.connection.is_connected():
				self.connect()
			result = None
			cursor = self.connection.cursor(dictionary=dictionary)
			try:
				cursor.execute(query)
				if fetchmode>1:
					result = cursor.fetchall()
				elif fetchmode==1:
					result = cursor.fetchone()
				else:
					result = True
			except Exception as e:
				print("ERROR: Query `{}` resulted in an error; `{}`".format(query, e))
			finally:
				cursor.close()
				if self.connection.is_connected():
					self.disconnect()
			return result
	
	class DBMeme(DB):
		def __init__(self, parent, id=None):
			super().__init__(parent.dbpassword)
			self.parent = parent
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
			
			self.cache_age = 0
			self.depth = -1 # depth is a value that can only increase, as it increases, the cache date applies to all of it
		
		@property
		def searchdata(self):
			if self.depth < 2: # all metadata is required for this task
				self.getmeme(depth=2)
			
			data = ''.join([desc.text for desc in self.descriptions])
			data += ''.join([trans.text for trans in self.transcriptions])
			data += ''.join([tag for tag in self.tags])
			data += ''.join([cat for cat in self.categories])
			data += self.type
			
			data = data.strip(' ').strip('\n').lower().replace('<br/>','')
			# could consider caching this..?
			
			return data
		
		async def post(self, ctx, owner=None, force=False):
			if self.id in self.parent.usedmemes[ctx.guild.id] and not force:
				return False
			
			self.parent.usedmemes[ctx.guild.id].append(self.id)
			
			if self.status == 404:
				await emformat.make_embed(ctx.channel, message='', title="Not found!", description="Unable to locate this meme, are you sure it exists?", author=None)
				return False
			if self.status == 403:
				await emformat.make_embed(ctx.channel, message='', title="Permission denied!", description="To view this meme, open the meme in MemeDB and login with an administrative account.", author=None, link=f"https://meme.yiays.com/meme/{self.id}" if self.in_db else '')
				return False
			if self.nsfw and not ctx.channel.is_nsfw():
				await emformat.make_embed(ctx.channel, message='', title="This meme is potentially nsfw!", description="The channel must be marked as nsfw for this meme to be shown.", author=None, link=f"https://meme.yiays.com/meme/{self.id}" if self.in_db else '')
				return False
			await emformat.make_embed(ctx.channel,
																message = '',
																title = "Meme" + (f" #{self.id} on MemeDB" if self.in_db else ''),
																description = self.url if self.type == 'text' else self.descriptions[0].text if len(self.descriptions) else f"This meme needs a description. *({globals.prefix_short}meme #{self.id} describe)*" if self.in_db else "Upvote this meme to add it to MemeDB!",
																color = self.color,
																author = "Posted by "+owner.mention if owner else None,
																image = self.url if self.type in ['image', 'gif'] else f"https://cdn.yiays.com/meme/{self.id}.thumb.jpg" if type in ['video', 'webm'] else '',
																fields = {
																	"categories": ', '.join([name for name in self.categories.keys()]) if len(self.categories) else f"None yet, you should suggest one! *({globals.prefix_short}meme #{self.id} cat)*",
																	"tags": ', '.join([name for name in self.tags.keys()]) if len(self.tags) else f"None yet, you should suggest some! *({globals.prefix_short}meme #{self.id} tag)*"
																} if self.in_db else {},
																link = f"https://meme.yiays.com/meme/{self.id}" if self.in_db else '')
			
			if self.type in ['audio', 'video', 'webm', 'url']: # Follow up with a link that should be automatically embedded in situations where we have to
				await ctx.channel.send(self.url)
			
			return True
		
		def fetch(self, id):
			query = self.selectquery(selects=['meme.*', 'IFNULL(AVG(edge.Rating),4) AS Edge'], _from='meme', joins=['LEFT JOIN edge ON meme.Id = edge.memeId'], wheres=['Id = '+str(id)], limit='1')
			
			return self.runquery(query, 1)
		
		def fetchall(self):
			# Builds cache of all memes in the database, cats and tags will need to be fetched later if and when needed
			query = self.selectquery(
				selects=[
					'meme.*',
					'description.Id AS descriptionId',
					'description.userId AS descriptionUserId',
					'description.Text AS descriptionText',
					'transcription.Id AS transcriptionId',
					'transcription.userId AS transcriptionUserId',
					'transcription.Text AS transcriptionText',
					'tag.Id AS tagId',
					'tag.Name AS tagName',
					'category.Id AS categoryId',
					'category.Name AS categoryName',
					'IFNULL(AVG(edge.Rating),4) AS Edge'
				],
				_from='meme',
				joins=[
					"LEFT JOIN description ON meme.Id = description.memeId",
					"LEFT JOIN transcription ON meme.Id = transcription.memeId",
					"LEFT JOIN categoryvote ON categoryvote.memeId = meme.Id",
					"LEFT JOIN category ON categoryvote.categoryId = category.Id",
					"LEFT JOIN tagvote ON tagvote.memeId = meme.Id",
					"LEFT JOIN tag ON tagvote.tagId = tag.Id",
					"LEFT JOIN edge ON meme.Id = edge.memeId"
				],
				groups=['description.Id', 'transcription.Id', 'tag.Id', 'category.Id', 'meme.Id'],
				orders=['meme.Id DESC']
			)
			
			lastid = -1
			for row in self.runquery(query, fetchmode=2):
				# meme
				if row['Id']!=lastid:
					if row['Id'] not in self.parent.memes:
						self.parent.memes[row['Id']] = Meme.DBMeme(self.parent)
					self.parent.memes[row['Id']].getmeme(depth=0, row=row)
				lastid = row['Id']
				
				targetmeme = self.parent.memes[row['Id']]
				
				# descriptions
				if row['descriptionId'] is not None:
					targetmeme.descriptions.append(Meme.DBDescription(id=row['descriptionId'], meme=targetmeme, author=row['descriptionUserId'], text=row['descriptionText'])) # editId may be needed later
				
				# transcriptions
				if row['transcriptionId'] is not None:
					targetmeme.transcriptions.append(Meme.DBTranscription(id=row['transcriptionId'], meme=targetmeme, author=row['transcriptionUserId'], text=row['transcriptionText'])) # editId may be needed later
				
				# categories
				if row['categoryId'] is not None:
					targetmeme.categories[row['categoryName']] = Meme.DBCategory(parent=self.parent, id=row['categoryId'], meme=targetmeme, name=row['categoryName']) # voters could be an issue eventually
				
				# tags
				if row['tagId'] is not None:
					targetmeme.tags[row['tagName']] = Meme.DBTag(parent=self.parent, id=row['tagId'], meme=targetmeme, name=row['tagName']) # voters could be an issue eventually
				
				targetmeme.depth = 2 # more or less...
				
		
		def getmeme(self, id=None, depth=2, row='fetchplz'):
			# depth 0; just the meme
			# depth 1; tags and cats
			# depth 2; everything: tags, cats, desc and trans
			if id is None: id = self.id
			else: self.id = id
			
			
			if self.in_db and self.cache_age > int(time.time()) - 60*60*24: # < cache lasts 24 hours
				if self.depth >= depth:
					return self
				else:
					if self.depth == 0:
						self.getcats()
						self.gettags()
						if depth > 1:
							self.getdescriptions()
							self.gettranscriptions()
					elif self.depth == 1:
						self.getdescriptions()
						self.gettranscriptions()
					
					# this doesn't increase the base cache because the base meme isn't fetched
					self.depth = max(depth, self.depth)
					return self
			
			if row == 'fetchplz':
				row = self.fetch(id)
			
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
					self.nsfw = True
					if self.edge >= 1.5:
						self.status = 403
				
				if depth >= 1:
					self.gettags()
					self.getcats()
					if depth >= 2:
						self.getdescriptions()
						self.gettranscriptions()
		
				self.cache_age = int(time.time())
				self.depth = max(depth, self.depth)
		
				self.parent.memes[self.id] = self
			
			else:
				print(f"ERROR: failed to fetch meme {self.id}!")
			
			return self
		
		def getdescriptions(self):
			query = self.selectquery(selects=['description.*'], _from='description', joins=['LEFT JOIN descvote ON description.Id = descvote.descId'], wheres=['memeId = '+str(self.id)], groups=['description.Id'], orders=['SUM(descvote.Value) DESC'])
			
			self.descriptions = []
			for row in self.runquery(query, 2):
				self.descriptions.append(Meme.DBDescription(id=row['Id'], meme=self, author=row['userId'], editid=row['editId'], text=row['Text']))
			
		def gettranscriptions(self):
			query = self.selectquery(selects=['transcription.*'], _from='transcription', joins=['LEFT JOIN transvote ON transcription.Id = transvote.transId'], wheres=['memeId = '+str(self.id)], groups=['transcription.Id'], orders=['SUM(transvote.Value) DESC'])
			
			self.transcriptions = []
			for row in self.runquery(query, 2):
				self.transcriptions.append(Meme.DBTranscription(id=row['Id'], meme=self, author=row['userId'], editid=row['editId'], text=row['Text']))
			
		
		def gettags(self):
			query = self.selectquery(selects=['tagvote.*', 'tag.*'], _from='tagvote', joins=['LEFT JOIN tag ON tagvote.tagId = tag.Id'], wheres=['memeId = '+str(self.id)])
			
			for row in self.runquery(query, 2):
				if row['Name'] not in self.tags:
					self.tags[row['Name']] = Meme.DBTag(parent=self.parent, id=row['Id'], meme=self, name=row['Name'], voters={})
				self.tags[row['Name']].voters[row['userId']] = row['Value']
			
			return self.tags
		
		def getcats(self):
			query = self.selectquery(selects=['categoryvote.*', 'category.*'], _from='categoryvote', joins=['LEFT JOIN category ON categoryvote.categoryId = category.Id'], wheres=['memeId = '+str(self.id)])
			
			for row in self.runquery(query, 2):
				if row['Name'] not in self.categories:
					self.categories[row['Name']] = Meme.DBCategory(parent=self.parent, id=row['Id'], meme=self, name=row['Name'], voters={})
				self.categories[row['Name']].voters[row['userId']] = row['Value']
			
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
		def __init__(self, parent, owner, search, result_type=None, include_tags=True, nsfw=False):
			super().__init__(parent.dbpassword)
			self.parent = parent
			self.owner = owner
			self.title = None
			self.search = search
			self.nsfw = nsfw
			self.result_type = Meme.DBMeme if result_type is None else result_type
			self.results = []
			self.message = None
			
			self.include_tags = include_tags
			self.tag_filters = {}
			self.cat_filters = {}
			self.edge_filter = 0
			
			self.searchre = {
				"edge": re.compile(r"edge:(\d)"),
				"tags": re.compile(r"([-])?tag:([\w\d\-_]+)"),
				"cats": re.compile(r"([-])?cat:([\w\d\-_]+)")
			}
			# Test cases:
			# 	edge:1 -tag:fnaf -tag:anime -cat:anime -cat:lowquality ばん
			#		edge:2 tag:shrek cat:anime
			
			self.alphanum = re.compile('[\W_]+')
			
			self.query = None
		
		def get_results(self):
			self.tag_filters = {'+':[], '-':[]}
			self.cat_filters = {'+':[], '-':[]}
			self.edge_filter = 1.5 if self.nsfw else 0.5
			
			title = []
			
			remainder = self.search
			
			edge_min = 1
			edge_max = 2 if self.owner.id not in globals.superusers else 4 #TODO: instead fetch the DBUser and check for Admin
			
			edge = self.searchre['edge'].match(self.search)
			if edge and edge.group(1).isdigit(): # sanity check
				target_edge = int(edge.group(1))
				self.edge_filter = min(max(target_edge, edge_min), edge_max)-0.5
				if target_edge != self.edge_filter: self.message = f"Warning: Your requested edge level is invalid or unavailable to your account, rounded to {self.edge_filter}"
				remainder = remainder.replace(edge.group(0),'')
			
			tags = self.searchre['tags'].findall(self.search)
			for tag in tags:
				modifier = tag[0]
				name = tag[1]
				
				match = utils.intuitivelistsearch(name.replace('-', ' ').replace('_', ' '), [dbtag.name for dbtag in self.parent.tags.values()])
				if match:
					self.tag_filters['-' if modifier == '-' else '+'].append([dbtag.id for dbtag in self.parent.tags.values() if dbtag.name == match][0])
					title.append(f"#{match}")
				else:
					self.title = "Invalid search"
					self.message = f"Couldn't find a tag by the name {name}!"
					return False
				
				remainder = remainder.replace('tag:'+name,'')
			
			cats = self.searchre['cats'].findall(self.search)
			catwheres = []
			for cat in cats:
				modifier = cat[0]
				name = cat[1]
				
				match = utils.intuitivelistsearch(name.replace('-', ' ').replace('_', ' '), [dbcat.name for dbcat in self.parent.categories.values()])
				if match:
					self.cat_filters['-' if modifier == '-' else '+'].append([dbcat.id for dbcat in self.parent.categories.values() if dbcat.name == match][0])
					title.append(f"{match}")
				else:
					self.title = "Invalid search"
					self.message = f"Couldn't find a category by the name {name}!"
					return False
				
				remainder = remainder.replace('cat:'+name,'')
			
			for meme in self.parent.memes.values():
				#edge search
				if meme.edge > self.edge_filter or meme.edge < self.edge_filter - 1.0:
					continue
				
				#text search - also inadvertently fetches tags and cats as a result
				if remainder:
					if remainder not in meme.searchdata:
						continue
				
				#tag search
				if self.tag_filters['-']:
					if set(tag.id for tag in meme.tags.values())&set(self.tag_filters['-']):
						continue
				if self.tag_filters['+']:
					if not (set(tag.id for tag in meme.tags.values())&set(self.tag_filters['+'])):
						continue
			
				#cat search
				if self.cat_filters['-']:
					if set(cat.id for cat in meme.categories.values())&set(self.cat_filters['-']):
						continue
				if self.cat_filters['+']:
					if not (set(cat.id for cat in meme.categories.values())&set(self.cat_filters['+'])):
						continue
				
				self.results.append(meme)
			
			self.title = "{} memes".format(', '.join(title))
			if remainder:
				self.title += f" which match the search term '{remainder}'"
			return self.results
		
		def pick(self, guild):
			for result in self.results:
				if result.id not in self.parent.usedmemes[guild]:
					return result
			return None
		
		async def post(self, ctx, n=1):
			await ctx.channel.send(f"**{self.title}** - {len(self.results)} results total.")
			if self.message:
				await ctx.channel.send(self.message)
				if not self.message.startswith("Warning: "): return False
			
			i = 0
			while i < int(n):
				meme = self.pick(ctx.guild.id)
				if meme is None:
					await ctx.channel.send(f"Can't find any{' more ' if len(self.results)>0 else ' '}memes with this query! Try a less specific search.")
					return False
				success = await meme.post(ctx)
				if success:
					i += 1
				await asyncio.sleep(1)
			return True
	
	class DBTag(DB):
		def __init__(self, parent, id=None, meme=None, name="", voters=None, popularity=None):
			super().__init__(parent.dbpassword)
			self.parent = parent
			self.id = id
			self.meme = meme
			self.name = name
			self.voters = voters if voters is not None else {}
			self.popularity = None
			
			if self.name!="":
				self.cache_age = int(time.time())
			
		def __str__(self):
			return self.name
		
		def fetchall(self):
			self.parent.tags = {}
			for row in self.runquery(self.selectquery(selects=['Id', 'Name', 'COUNT(tagId) AS Popularity'], _from='tag', joins=['LEFT JOIN tagvote ON tag.Id=tagvote.tagId'], groups=['Id']), fetchmode=2):
				self.parent.tags[row['Id']] = Meme.DBTag(parent=self.parent, id=row['Id'], name=row['Name'], popularity=row['Popularity'])
	
	class DBCategory(DB):
		def __init__(self, parent, id=None, meme=None, name="", description="", voters=None, popularity=None):
			super().__init__(parent.dbpassword)
			self.parent = parent
			self.id = id
			self.meme = meme
			self.name = name
			self.description = description
			self.voters = voters if voters is not None else {}
			self.popularity = popularity
			
			if self.name!="":
				self.cache_age = int(time.time())
			
		def __str__(self):
			return self.name
	
		def fetchall(self):
			self.parent.categories = {}
			for row in self.runquery(self.selectquery(selects=['Id', 'Name', 'Description', 'COUNT(categoryId) AS Popularity'], _from='category', joins=['LEFT JOIN categoryvote ON category.Id=categoryvote.categoryId'], groups=['Id']), fetchmode=2):
				self.parent.categories[row['Name']] = Meme.DBCategory(parent=self.parent, id=row['Id'], name=row['Name'], description=row['Description'], popularity=row['Popularity'])
	
	class DBDescription():
		def __init__(self, id=None, meme=None, author=None, editid=None, text="", voters=None):
			self.id = id
			self.meme = meme
			self.author = author
			self.editid = editid
			self.text = text
			self.voters = voters if voters is not None else {}
		
		def __str__(self):
			return self.text
	
	class DBTranscription():
		def __init__(self, id=None, meme=None, author=None, editid=None, text="", voters=None):
			self.id = id
			self.meme = meme
			self.author = author
			self.editid = editid
			self.text = text
			self.voters = voters if voters is not None else {}
		
		def __str__(self):
			return self.text
	
	class DBUser(DB):
		def __init__(self, parent, id=None, username=None, discriminator=None):
			super().__init__(parent.dbpassword)
			self.parent = parent
			self.id = id
			self.username = username
			self.discriminator = discriminator
			self.favourites = {}
			self.is_admin = False
			self.is_banned = False
		
		def fetch(self, id=None):
			if id is None: id = self.id
			else: self.id = id
			
			query = self.selectquery(selects=['user.*'], _from='user', wheres=['user.Id = '+str(id)])
			
			row = self.runquery(query, 1)
			
			self.username = row['Username']
			self.discriminator = row['Discriminator']
			self.is_admin = row['Admin']
			self.is_banned = row['Banned']
	
	async def BackgroundService(self,skip=0):
		if globals.logchannel: await self.bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - starting background service...")
		try:
			pass
			"""
			for channel in [m.id for m in globals.memesources][skip:]:
				counter = 0
				channel=self.bot.get_channel(channel)
				print('BS: iterating upon #'+channel.name+'...')
				print("BS: 0",end='\r')
				async for message in channel.history(limit=10000):
					counter+=1
					print('BS: '+str(counter),end='\r')
					await self.ReactionCrawler(message,channel)
			print('BS: done')
			"""
		except Exception as e:
			if globals.logchannel and self.bot.is_ready(): await self.bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - background service failed to complete!```"+str(e)+"```")
		else:
			if globals.logchannel and self.bot.is_ready(): await self.bot.get_channel(globals.logchannel).send(time.strftime("%H:%M:%S",time.localtime())+" - background service ended.")
	
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
			for memechannel in globals.memesources:
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

	async def on_message(self, message):
		if message.channel.id in [m.id for m in globals.memesources]:
			self.OnMemePosted(message)

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
	
	async def on_raw_reaction_add(self, e):
		if e.channel_id in [m.id for m in globals.memesources] and e.user_id != bot.user.id:
			await self.OnReaction(True,e.message_id,e.user_id,e.channel_id,e.emoji)
	
	async def on_raw_reaction_remove(self, e):
		if e.channel_id in [m.id for m in globals.memesources]:
			await self.OnReaction(False,e.message_id,e.user_id)
	
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
				if ctx.channel.is_nsfw():
					meme = random.choice([meme for meme in self.memes.values() if meme.edge < 1.5])
				else:
					meme = random.choice([meme for meme in self.memes.values() if not meme.nsfw and meme.edge < 0.5])
				success = await meme.post(ctx)
				if success:
					i += 1
				await asyncio.sleep(1)
		
		elif n[0] == '#' and n[1:].isdigit(): # meme by id
			if globals.verbose: print('meme id command')
			id=n[1:]
			if id not in self.memes.keys():
				meme = Meme.DBMeme(parent=self, id=id)
			else:
				meme = self.memes[id]
			meme.getmeme(depth=2)
			await meme.post(ctx, force=True)
		
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
			if searchargs[-1].isdigit(): # meme search (query) n
				search = ' '.join(searchargs[:-1])
				n = min(int(searchargs[-1]), 10)
			
			if search not in self.searches:
				async with ctx.channel.typing():
					searcher = Meme.DBSearch(parent=self, owner=ctx.message.author, search=search, result_type=Meme.DBMeme, include_tags=True, nsfw=ctx.channel.is_nsfw())
					searcher.get_results()
					self.searches[search] = searcher
			else:
				searcher = self.searches[search]
				searcher.owner = ctx.message.author
				searcher.get_results()
			
			await searcher.post(ctx, n=n)

