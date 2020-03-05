import globals
import emformat
import censor
import asyncio
import discord
from discord.ext import commands
import pprint
import urllib, json
import aiohttp, re, random, html
from bs4 import BeautifulSoup

globals.commandlist['google']=['google','image']

class Search(commands.Cog):
	"""Google related commands."""
	def __init__(self, bot):
		self.bot = bot
		self.results={}
		self.imgs={}
	
	async def imgscrape(self,query):
		url="https://www.google.com/search?q="+urllib.parse.quote(query,safe='')+"&source=lnms&tbm=isch&gws_rd=cr"
		url=url.replace('%20','+')
		header={'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}
		attempts = 0
		async with aiohttp.ClientSession() as session:
			while attempts < 4:
				async with session.get(url,headers=header) as r:
					if r.status == 200:
						a = await r.text()
						with open(globals.store+"imgscrape.html",'w',encoding='utf-8') as file:
							file.write(a)
						autocorrect=re.search('Showing results for.+?<i>(.+?)</i>',a)
						if autocorrect!=None: autocorrect=autocorrect.group()
						else: autocorrect=''
						image_list = re.findall(""","ou":"(http[s]?://[A-z0-9:/?&.%_()-]*?)","ow":""",a)
						if(len(image_list)):
							return (image_list,autocorrect)
						else:
							redirect = re.findall(r"""Please click <a href="(\/search\?q=[\w\d+&;=-]+)">here<\/a> if you are not redirected within a few seconds\.""",a)
							if len(redirect):
								url = "https://www.google.com"+redirect[0]
								print("Detecting another redirect! "+url)
								attempts += 1
							else:
								raise Exception("ImageSearch: Couldn't find any images. On adition to that, merely also couldn't a path towards more images.")
					else:
						raise Exception("ImageSearch: GET {} failed: Error code {}".format(url,r.status))
			raise Exception("ImageSearch: It appears that google has completely blocked this bot.")
	
	def html2discord(self,input):
		input=input.replace('<i>','*')
		input=input.replace('</i>','*')
		input=input.replace('<b>','**')
		input=input.replace('</b>','**')
		input=input.replace(' <br>','')
		input=input.replace('<br> ','')
		input=input.replace('<br>',' ')
		input=html.unescape(input)
		input=re.sub(r'\<.*\>','',input)
		
		return input
	
	async def googscrape(self,query):
		url=urllib.parse.quote(query,safe='')
		url=url.replace('%20','+')
		header={'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'}
		async with aiohttp.ClientSession() as session:
			async with session.get("http://www.google.com/search?q="+url+"&gws_rd=cr",headers=header) as r:
				if r.status == 200:
					a = await r.text()
					a = a.replace('\n',' ')
					
					result_list={'url':[],'title':[],'description':[]}
					
					i=0
					s_url=re.findall('<h3 class=\"r\"><a href=\"(.+?)\"',a)
					s_description=re.findall('<span class=\"st\">(.+?)</span>',a)
					print(str(len(s_url))+', '+str(len(s_description)))
					for url,description in zip(s_url,s_description):
						if i<5:
							result_list['url'].append(self.html2discord(url))
							result_list['title'].append(self.html2discord(re.findall('<h3 class=\"r\"><a href=\"'+re.escape(url)+'\">(.+?)</a></h3>',a)[0]))
							result_list['description'].append(self.html2discord(description))
							i+=1
					
					return result_list
				else:
					print('google search: error '+str(r.status))
					return({})

	@commands.command(pass_context=True, no_pm=False, aliases=['gsearch','search'])
	async def google(self, ctx, *, query=''):
		"""Search Google."""
		if not (ctx.message.guild.id not in self.results or self.results[ctx.message.guild.id]==None) and query=='more': #show top 5 google search results
			if globals.verbose: print('google more command')
			results={}
			for i in range(max(5,len(self.results[ctx.message.guild.id]['title']))):
				results[self.results[ctx.message.guild.id]['title'][i]]=self.results[ctx.message.guild.id]['description'][i]+' - [read more](https://www.google.com'+self.results[ctx.message.guild.id]['url'][i]+')'
			await emformat.make_embed(ctx.message.channel,"here's some more results...",
				query,"showing the top 5 results.",0x4385F6,'google.com',globals.emurl+'result.gif',
				results,
				"merely v"+globals.ver+" - created by Yiays#5930",
				globals.iconurl,
				"http://www.google.com/search?q="+urllib.parse.quote(query,safe='').replace('%20','+'))
			self.results[ctx.message.guild.id]=None
		else:
			if globals.verbose: print('google command')
			if query=='':
				await emformat.genericmsg(ctx.message.channel,globals.dhelp['google'],'help','google')
				return
			danger=censor.dangerous(query)
			if danger and not ctx.message.channel.is_nsfw():
				nope=censor.sass()
				nope+="\ni found these filthy words in your search; `"+(', '.join({*danger}))+"`"
				await emformat.genericmsg(ctx.message.channel,nope,'error','google')
				return
			async with ctx.message.channel.typing():
				print("searching for '"+query+"'...")
				self.results[ctx.message.guild.id]=await self.googscrape(query)
				print("complete!")
				if self.results[ctx.message.guild.id]['title']:
					await emformat.make_embed(ctx.message.channel,"here's what I found...",
						query,"showing the top result.\ntype `merely google more` for more results.",
						0x4385F6,'google.com',globals.emurl+'result.gif',
						{self.results[ctx.message.guild.id]['title'][0]:self.results[ctx.message.guild.id]['description'][0]+' - [read more](https://www.google.com'+self.results[ctx.message.guild.id]['url'][0]+')'},
						"merely v"+globals.ver+" - created by Yiays#5930",
						globals.iconurl,
						"http://www.google.com/search?q="+urllib.parse.quote(query,safe='').replace('%20','+'))
				else:
					await ctx.message.channel.send("it appears that google has completely blocked this bot.")
	@google.error
	async def google_error(self,ctx,error):
		print(error)
		await emformat.genericmsg(ctx.message.channel,"something went wrong when trying to fulfil your search! please try another search term.","error","google")
	
	@commands.command(pass_context=True, no_pm=False, aliases=['images','gimage','googleimage','gimages','googleimages'])
	async def image(self, ctx, *, query=''):
		"""Search Google Images"""
		if globals.verbose: print('google images command')
		if query=='':
			await emformat.genericmsg(ctx.message.channel,globals.dhelp['image'],'help','image')
		if query=='more' and ctx.message.guild.id in self.imgs and self.imgs[ctx.message.guild.id]!=None:
			await ctx.message.delete()
			await self.sendimgs(ctx.message.channel,self.imgs[ctx.message.guild.id],5)
		else:
			if not ctx.message.channel.is_nsfw():
				danger=censor.dangerous(query)
			else: danger=False
			if danger: #cancel search if the query is dangerous
				nope=censor.sass()
				nope+="\ni found these filthy words in your search; `"+(', '.join({*danger}))+"`"
				await emformat.genericmsg(ctx.message.channel,nope,'error','image')
			else:
				async with ctx.message.channel.typing():
					nsfw=100
					if not ctx.message.channel.is_nsfw():
						query+=' -nsfw'
						nsfw=-6
					if globals.verbose: print("image searching for '"+query+"'...")
					imglist, autocorrect = await self.imgscrape(query)
					if globals.verbose: print("search complete!")
					
					if len(autocorrect)>0 and autocorrect!=query[:nsfw] and not ctx.message.channel.is_nsfw():
						if globals.verbose: print(f"'{query}' was autocorrected to '{autocorrect}'!")
						danger=censor.dangerous(autocorrect)
					else: danger=False
					if danger: #don't show search results if google autocorrected them to something nefarious.
						nope=censor.sass()
						nope+="\ni found these filthy words in your *autocorrected* search; `"+(', '.join({*danger}))+"`"
						await emformat.genericmsg(ctx.message.channel,nope,'error','image')
					else:
						self.imgs[ctx.message.guild.id]=imglist
						if ctx.invoked_with.lower() in ['images','gimages','googleimages']:
							await self.sendimgs(ctx.message.channel,imglist,1)
							await self.sendimgs(ctx.message.channel,imglist,5)
						else:
							await self.sendimgs(ctx.message.channel,imglist,1)
	@image.error
	async def image_error(self,ctx,error):
		print(error)
		await emformat.genericmsg(ctx.message.channel,"something went wrong when trying to fulfil your image search! please try another search term.\n```"+str(error)+"```","error","image")
	
	async def sendimgs(self,channel,imglist,count):
		if len(imglist)>=1:
			if channel.guild.get_member(self.bot.user.id).permissions_in(channel).embed_links:
				for _ in range(0 if count==1 else 1,min(count,len(imglist))):
					em=discord.Embed(type='rich')
					em.set_image(url=imglist[0 if count==1 else 1])
					await channel.send(embed=em)
					if count>1: del imglist[1]
					
				if count==1 and random.choice(range(3))==1: await channel.send("you can get more results by typing `merely image more`")
			else:
				await channel.send('unable to show images without `EMBED_LINKS` permission!')
		else:
			await emformat.genericmsg(channel,"no results found!",'error','image')