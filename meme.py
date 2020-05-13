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

class Meme(commands.Cog):
	"""Database and API for collecting, organizing and presenting memes"""
	def __init__(self, bot, dbpassword):
		self.bot = bot
		self.dbpassword = dbpassword
		self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60))
		self.memes = {}
		self.searches = {}
		self.usedmemes = Meme.UsedMemes(self) #TODO: make usedmemes specific to the guild
		self.users = {}
		
		if globals.verbose: print("filling meme tags/categories cache...")
		self.tags = {}
		Meme.DBTag(self).fetchall()
		self.categories = {}
		Meme.DBCategory(self).fetchall()
		if globals.verbose: print("meme tags/categories cache done!")
	
	def __delete__(self,instance):
		self.session.close()
	
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
		
		async def post(self, channel, owner=None, force=False):
			if self.id in self.parent.usedmemes and not force:
				return False
			
			self.parent.usedmemes.append(self.id)
			
			if self.status == 404:
				await emformat.make_embed(channel, message='', title="Not found!", description="Unable to locate this meme, are you sure it exists?", author=None)
				return False
			if self.status == 403:
				await emformat.make_embed(channel, message='', title="Permission denied!", description="To view this meme, open the meme in MemeDB and login with an administrative account.", author=None, link=f"https://meme.yiays.com/meme/{self.id}" if self.in_db else '')
				return False
			if self.nsfw and not channel.is_nsfw():
				await emformat.make_embed(channel, message='', title="This meme is potentially nsfw!", description="The channel must be marked as nsfw for this meme to be shown.", author=None, link=f"https://meme.yiays.com/meme/{self.id}" if self.in_db else '')
				return False
			await emformat.make_embed(channel,
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
				await channel.send(self.url)
			
			return True
		
		def fetch(self, id, depth=2):
			query = self.selectquery(selects=['meme.*', 'IFNULL(AVG(edge.Rating),4) AS Edge'], _from='meme', joins=['LEFT JOIN edge ON meme.Id = edge.memeId'], wheres=['Id = '+str(id)], limit='1')
			
			return self.runquery(query, 1)
		
		def getrandom(self, depth=2, nsfw=False):
			#TODO This query is too complex for the constructor. Fix that.
			query = \
			f"""
				SELECT r1.*, IFNULL(AVG(edge.Rating),4) AS Edge
				FROM (meme AS r1 LEFT JOIN edge ON Id = edge.memeId)
				JOIN (SELECT CEIL(RAND() * (SELECT MAX(Id) FROM meme)) AS maxId) AS r2
				WHERE r1.Id >= r2.maxId
				HAVING Edge < {"0.5" if not nsfw else "1.5"}
				ORDER BY r1.Id ASC
				LIMIT 1
			"""
			
			row = self.runquery(query, 1)
			
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
		
				self.parent.memes[self.id] = self
			
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
		def __init__(self, parent, search, result_type=None, include_tags=True):
			super().__init__(parent.dbpassword)
			self.parent = parent
			self.search = search
			self.result_type = Meme.DBMeme if result_type is None else result_type
			self.results = []
			self.include_tags = include_tags
			
			self.searchre = {
				"edge": re.compile(r"([🌶]{1,4})"),
				"tags": re.compile(r"([-])?#(\w+)"),
				"cats": re.compile(r"([-])?\$(\w+)")
			}
			# Test cases:
			# 	🌶 -#fnaf -#anime -$anime -#lowquality ばん
			#		🌶🌶 #shrek $anime
			
			self.alphanum = re.compile('[\W_]+')
			
			self.query = None
		
		def construct(self):
			selects = []
			_from		= ''
			joins		= []
			wheres  = []
			groups	= []
			havings = []
			orders	= ['meme.Id DESC']
			limit		= ""
			
			if self.result_type is Meme.DBMeme:
				self.connect()
				
				# Basic meme search query
				_from = "meme"
				selects.append("meme.*")
				selects.append("IFNULL(AVG(edge.Rating),4) AS Edge")
				# THIS MUST REMAIN AS INDEX #2
				selects.append("""
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
					,'<br/>','') AS SearchData"""
				)
				joins += [
					"LEFT JOIN description ON meme.Id = description.memeId",
					"LEFT JOIN transcription ON meme.Id = transcription.memeId",
					"LEFT JOIN categoryvote ON categoryvote.memeId = meme.Id",
					"LEFT JOIN category ON categoryvote.categoryId = category.Id",
					"LEFT JOIN tagvote ON tagvote.memeId = meme.Id",
					"LEFT JOIN tag ON tagvote.tagId = tag.Id",
					"LEFT JOIN edge ON meme.Id = edge.memeId"
				]
				groups.append("meme.Id")
				limit = "20"
				
				# Tags search
				if self.include_tags:
					remainder = self.search
					
					edge = self.searchre['edge'].match(self.search)
					if edge:
						havings.append(f"Edge <= {len(edge.group(1))-0.5}")
						
						remainder = remainder.replace('🌶','')
					
					tags = self.searchre['tags'].findall(self.search)
					tagwheres = []
					for tag in tags:
						modifier = tag[0]
						name = tag[1]
						
						for dbtag in self.parent.tags.values():
							if name in self.alphanum.sub('', dbtag.name).lower():
								tagwheres.append(f"tag.Id {'!=' if modifier=='-' else '='} {dbtag.id}")
						
						remainder = remainder.replace('#'+name,'')
					if len(tagwheres)>0:
						wheres.append('('+' OR '.join(tagwheres)+')')
					elif len(tags)>0:
						wheres.append('tag.Id = -1')
					
					cats = self.searchre['cats'].findall(self.search)
					catwheres = []
					for cat in cats:
						modifier = cat[0]
						name = cat[1]
						
						for dbcat in self.parent.categories.values():
							if name in self.alphanum.sub('', dbcat.name).lower():
								catwheres.append(f"category.Id {'!=' if modifier=='-' else '='} {dbcat.id}")
						
						remainder = remainder.replace('$'+name,'')
					if len(catwheres)>0:
						wheres.append('('+' OR '.join(catwheres)+')')
					elif len(cats)>0:
						wheres.append('category.Id = -1')
					
					remainder = remainder.lower().replace(' ','')
					if remainder:
						havings.append(f"SearchData LIKE \"%{self.connection.converter.escape(remainder)}%\"")
					else:
						selects.pop(2) # speed up searches when there's no searchdata
				else:
					havings.append(f"SearchData LIKE \"%{self.connection.converter.escape(self.search.lower().replace(' ',''))}%\"")
						
			#TODO: add support for more types
			else:
				raise TypeError("Unsupported type: {}".format(self.result_type.__name__))
			
			self.query = self.selectquery(selects=selects, _from=_from, joins=joins, wheres=wheres, groups=groups, havings=havings, orders=orders, limit=limit)
			print(self.query)
			return self.query
		
		def fetch(self):
			if self.cache_age > int(time.time()) - 60*60*24:
				return self.results
			
			if self.query is None:
				self.construct()
			
			for row in self.runquery(self.query, 2):
				if row['Id'] not in self.parent.memes:
					self.parent.memes[row['Id']] = Meme.DBMeme(parent = self.parent)
				self.parent.memes[row['Id']].getmeme(id=row['Id'], row=row)
				self.results.append(self.parent.memes[row['Id']])
			
			self.cache_age = int(time.time())
			return self.results
		
		def pick(self):
			for result in self.results:
				if result.id not in self.parent.usedmemes:
					return result
			return None
		
		async def post(self, channel, n=1):
			i = 0
			while i < int(n):
				meme = self.pick()
				if meme is None:
					await channel.send(f"Can't find any{' more' if len(self.results)>0 else ''} memes with this query! Try a less specific search.")
					return False
				success = await meme.post(channel)
				if success:
					i += 1
				await asyncio.sleep(1)
	
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
				meme = Meme.DBMeme(parent=self).getrandom(nsfw=ctx.channel.is_nsfw())
				self.memes[meme.id] = meme
				success = await meme.post(ctx.channel)
				if success:
					i += 1
				await asyncio.sleep(1)
		
		elif n[0] == '#' and n[1:].isdigit(): # meme by id
			if globals.verbose: print('meme id command')
			id=n[1:]
			if id not in self.memes.keys():
				meme = Meme.DBMeme(parent=self, id=id)
			else:
				meme = memes[id]
			meme.getmeme()
			await meme.post(ctx.channel, force=True)
		
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
					searcher = Meme.DBSearch(parent=self, search=search, result_type=Meme.DBMeme, include_tags=True)
					searcher.construct()
					searcher.fetch()
					self.searches[search] = searcher
			else:
				searcher = self.searches[search]
				searcher.fetch()
			
			await searcher.post(ctx.channel, n=n)

