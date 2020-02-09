import globals
import emformat
import asyncio
import discord
from discord.ext import commands
import mysql.connector
import random
import re

globals.commandlist['tools']=['shorten']

class Tools(commands.Cog):
	"""Tools for all users"""
	def __init__(self, bot):
		self.bot = bot
		self.validurl = re.compile(
			r'^(?:http|ftp)s?://' # http:// or https://
			r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
			r'localhost|' #localhost...
			r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
			r'(?::\d+)?' # optional port
			r'(?:/?|[/?]\S+)$', re.IGNORECASE
		)

	@commands.command(pass_context=True, no_pm=False, aliases=['short','shorturl','urlshort','urlshortener','shrink','shrinkurl','urlshrink','urlshrinker','shortlink','linkshort','linkshortener','shrinklink','linkshrink','linkshrinker'])
	async def shorten(self, ctx, long='', short=''):
		"""Shorten a provided url using l.yiays.com"""
		if globals.verbose: print('shorten command')
		if long=='':
			await emformat.genericmsg(ctx.message.channel,globals.dhelp['shorten'],'help','shorten')
		else:
			if(re.match(self.validurl, long) is None):
				await ctx.channel.send("the provided url is invalid.")
			else:
				rand = False
				done = False
				if short == '':
					msg = await ctx.channel.send("if you would like a custom name for the url, say it now. ie. l.yiays.com/*merely* (type 0 if you would like a random url)")
					def check(m):
						return m.channel == ctx.channel and m.author == ctx.message.author
					msg = await self.bot.wait_for('message', check=check)
					short = msg.content
				mydb = mysql.connector.connect(host='192.168.1.120',user='meme',password=globals.memedbpass,database='linkshortener')
				while not done:
					if short == '0' or rand:
						rand = True
						chars = [chr(i) for i in list(range(48,57)) + list(range(65,90)) + list(range(97,122))]
						short = ''.join([random.choice(chars) for _ in range(random.randint(3,6))])
					cursor = mydb.cursor()
					cursor.execute("SELECT short FROM link WHERE short = %s", (short,))
					cursor.fetchall()
					if cursor.rowcount == 0:
						cursor.execute("INSERT INTO link(short, original, discordId) VALUES(%s, %s, %s)", (short, long, ctx.author.id))
						mydb.commit()
						cursor.close()
						await ctx.channel.send("done - *shortened by {} character(s)*: {}".format(len(long)-(len(short)+12),"https://l.yiays.com/"+short))
						done = True
