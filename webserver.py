import psutil, json, random
import globals
from aiohttp import web
from discord.ext import commands

class Webserver(commands.Cog):
	"""A simple api server"""
	def __init__(self, bot):
		self.bot = bot
		self.routes = web.RouteTableDef()
		
		self.app=web.Application()
		self.app.add_routes([web.get('/', self.index),
												 web.get('/changes', self.changes),
												 web.get('/stats', self.statsapi),
												 web.get('/dhelp', self.dhelp)])
		self.runner=web.AppRunner(self.app)
	
	async def start(self):
		await self.runner.setup()
		site = web.TCPSite(self.runner,'0.0.0.0',globals.apiport)
		await site.start()
	
	async def stop(self):
		await self.runner.cleanup()
	
	async def statsapi(self, request):
		#if globals.verbose: print('GET /stats')
		stats={
			'status': self.bot.cogs['Stats'].status,
			'exposure': self.bot.cogs['Stats'].exposure,
			'responses': self.bot.cogs['Stats'].responses,
			'uptime': self.bot.cogs['Stats'].uptime,
			'modules': self.bot.cogs['Stats'].modules,
			'library': self.bot.cogs['Stats'].library,
			'core': self.bot.cogs['Stats'].core,
			#'memes': self.bot.cogs['Stats'].memes,
			'cpu_usage': self.bot.cogs['Stats'].cpu_usage,
			'ram_usage': self.bot.cogs['Stats'].ram_usage,
			'hardware': self.bot.cogs['Stats'].hardware,
			'gentime': self.bot.cogs['Stats'].gentime,
			'raw':{
				'servers':len(self.bot.guilds),
				'sentcount':self.bot.cogs['Stats'].sentcount,
				'recievedcount':self.bot.cogs['Stats'].recievedcount,
				'uptime_d':self.bot.cogs['Stats'].d,
				'uptime_h':self.bot.cogs['Stats'].h,
				'uptime_m':self.bot.cogs['Stats'].m,
				'uptime_s':self.bot.cogs['Stats'].s,
				'ram_used':psutil.virtual_memory().used/1000000,
				'ram_total':psutil.virtual_memory().total/1000000
			}
		}
		return web.Response(text=json.dumps(stats),status=200,headers={'Access-Control-Allow-Origin':'https://merely.yiays.com',
																											'Cache-Control':'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0',
																											'Pragma':'no-cache',
																											'content-type':'application/json'})
	
	async def dhelp(self, request):
		if globals.verbose: print('GET /dhelp')
		return web.Response(text=json.dumps(globals.dhelp),status=200,headers={'Access-Control-Allow-Origin':'https://merely.yiays.com',
																											'Cache-Control':'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0',
																											'Pragma':'no-cache',
																											'content-type':'application/json'})
	
	async def index(self, request):
		if globals.verbose: print('GET /')
		return web.Response(text="{'status':'up'}", status=200, headers={'Access-Control-Allow-Origin':'https://merely.yiays.com',
																											'content-type':'application/json'})
	
	async def changes(self, request):
		if globals.verbose: print('GET /changes')
		return web.Response(text=''.join(globals.changes),status=200,headers={'Access-Control-Allow-Origin':'https://merely.yiays.com',
																											'Cache-Control':'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0',
																											'Pragma':'no-cache',
																											'content-type':'text/markdown'})