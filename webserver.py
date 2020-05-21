import psutil, json, random
import globals
from aiohttp import web
from discord.ext import commands

class Webserver(commands.Cog):
	"""A webserver, no commands included"""
	def __init__(self, bot):
		self.bot = bot
		self.routes = web.RouteTableDef()
		
		self.app=web.Application()
		self.app.add_routes([web.get('/', self.index),
												 web.get('/index.html', self.index),
												 web.get('/main.css', self.maincss),
												 web.get('/main.js', self.mainjs),
												 web.get('/stats.html', self.stats),
												 web.get('/stats.css', self.statscss),
												 web.get('/stats.js', self.statsjs),
												 web.get('/changes.html', self.changes),
												 web.get('/changes.js', self.changesjs),
												 web.get('/stats', self.statsapi),
												 web.get('/dhelp', self.dhelp),
												 web.get('/lacket', self.lacket),
												 web.get('/favicon.ico', self.favicon)])
		self.runner=web.AppRunner(self.app)
		self.site = None
		
		self.bot.events['on_ready'].append(start)
	
	async def start(self):
		if self.site is None:
			await self.runner.setup()
			self.site = web.TCPSite(self.runner,'0.0.0.0',globals.apiport)
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
				'members':sum([len(s.members) for s in self.bot.guilds]),
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
		with open('templates/index.html',encoding='utf8') as f:
			file=f.read().replace('{$globals.ver}',globals.ver)
		return web.Response(text=file,status=200,headers={'Access-Control-Allow-Origin':'https://merely.yiays.com','content-type':'text/html'})
	async def maincss(self, request):
		if globals.verbose: print('GET /main.css')
		with open('templates/main.css',encoding='utf8') as f:
			file=f.read()
		return web.Response(text=file,status=200,headers={'content-type':'text/css'})
	async def mainjs(self, request):
		if globals.verbose: print('GET /main.js')
		with open('templates/main.js',encoding='utf8') as f:
			file=f.read()
		return web.Response(text=file,status=200,headers={'content-type':'application/javascript'})
	
	async def stats(self, request):
		if globals.verbose: print('GET /stats.html')
		with open('templates/stats.html',encoding='utf8') as f:
			file=f.read()
		return web.Response(text=file,status=200,headers={'content-type':'text/html'})
	async def statscss(self, request):
		if globals.verbose: print('GET /stats.css')
		with open('templates/stats.css',encoding='utf8') as f:
			file=f.read()
		return web.Response(text=file,status=200,headers={'content-type':'text/css'})
	async def statsjs(self, request):
		if globals.verbose: print('GET /stats.js')
		with open('templates/stats.js',encoding='utf8') as f:
			file=f.read()
		return web.Response(text=file,status=200,headers={'content-type':'application/javascript'})
	
	async def changes(self, request):
		if globals.verbose: print('GET /changes.html')
		with open('templates/changes.html',encoding='utf8') as f:
			file=f.read().replace('{$globals.ver}',globals.ver).replace('{$changes}',''.join(globals.changes))
		return web.Response(text=file,status=200,headers={'content-type':'text/html'})
	async def changesjs(self, request):
		if globals.verbose: print('GET /changes.js')
		with open('templates/changes.js',encoding='utf8') as f:
			file=f.read()
		return web.Response(text=file,status=200,headers={'content-type':'application/javascript'})
	
	async def lacket(self, request):
		if globals.verbose: print('GET /lacket')
		with open('templates/lacket.html',encoding='utf8') as f:
			file=f.read().replace('{$globals.ver}',globals.ver)
		return web.Response(text=file,status=200,headers={'Access-Control-Allow-Origin':'https://merely.yiays.com','content-type':'text/html'})
	
	async def favicon(self, request):
		if globals.verbose: print('GET /favicon.ico')
		return web.Response(text='',status=404,headers={'content-type':'image/x-icon'})