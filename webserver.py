import psutil, json, random
import globals
from aiohttp import web

routes = web.RouteTableDef()

@routes.get('/stats')
async def stats(request):
	if globals.verbose: print('GET /stats')
	stats={
		'status': globals.stats.status,
		'exposure': globals.stats.exposure,
		'responses': globals.stats.responses,
		'uptime': globals.stats.uptime,
		'modules': globals.stats.modules,
		'library': globals.stats.library,
		'core': globals.stats.core,
		'memes': globals.stats.memes,
		'cpu_usage': globals.stats.cpu_usage,
		'ram_usage': globals.stats.ram_usage,
		'hardware': globals.stats.hardware,
		'generated time': globals.stats.gentime,
		'raw':{
			'servers':len(globals.bot.guilds),
			'members':sum([len(s.members) for s in globals.bot.guilds]),
			'sentcount':globals.stats.sentcount,
			'recievedcount':globals.stats.recievedcount,
			'uptime_d':globals.stats.d,
			'uptime_h':globals.stats.h,
			'uptime_m':globals.stats.m,
			'uptime_s':globals.stats.s,
			'ram_used':psutil.virtual_memory().used/1000000,
			'ram_total':psutil.virtual_memory().total/1000000
		}
	}
	return web.Response(text=json.dumps(stats),status=200,headers={'Access-Control-Allow-Origin':'https://merely.yiays.com',
																						 'Cache-Control':'no-store, no-cache, must-revalidate, max-age=0',
																						 'Cache-Control':'post-check=0, pre-check=0',
																						 'Pragma':'no-cache',
																						 'content-type':'application/json'})

@routes.get("/dhelp")
async def dhelp(request):
	if globals.verbose: print('GET /dhelp')
	return web.Response(text=json.dumps(globals.dhelp),status=200,headers={'Access-Control-Allow-Origin':'https://merely.yiays.com',
																										 'Cache-Control':'no-store, no-cache, must-revalidate, max-age=0',
																										 'Cache-Control':'post-check=0, pre-check=0',
																										 'Pragma':'no-cache',
																										 'content-type':'application/json'})

@routes.get("/")
@routes.get("/index.html")
async def index(request):
	if globals.verbose: print('GET /')
	with open(globals.store+'memes.txt','r',encoding='utf8') as m:
		memelist=m.readlines()
	meme=memelist[random.choice(range(len(memelist)))]
	with open('templates/index.html',encoding='utf8') as f:
		file=f.read().replace('{$globals.ver}',globals.ver).replace('{$meme}',meme)
	return web.Response(text=file,status=200,headers={'Access-Control-Allow-Origin':'https://merely.yiays.com','content-type':'text/html'})
@routes.get("/main.css")
async def css(request):
	if globals.verbose: print('GET /main.css')
	with open('templates/main.css',encoding='utf8') as f:
		file=f.read()
	return web.Response(text=file,status=200,headers={'content-type':'text/css'})
@routes.get("/main.js")
async def js(request):
	if globals.verbose: print('GET /main.js')
	with open('templates/main.js',encoding='utf8') as f:
		file=f.read()
	return web.Response(text=file,status=200,headers={'content-type':'application/javascript'})

@routes.get("/stats.html")
async def css(request):
	if globals.verbose: print('GET /stats.html')
	with open('templates/stats.html',encoding='utf8') as f:
		file=f.read()
	return web.Response(text=file,status=200,headers={'content-type':'text/html'})
@routes.get("/stats.css")
async def css(request):
	if globals.verbose: print('GET /stats.css')
	with open('templates/stats.css',encoding='utf8') as f:
		file=f.read()
	return web.Response(text=file,status=200,headers={'content-type':'text/css'})
@routes.get("/stats.js")
async def js(request):
	if globals.verbose: print('GET /stats.js')
	with open('templates/stats.js',encoding='utf8') as f:
		file=f.read()
	return web.Response(text=file,status=200,headers={'content-type':'application/javascript'})
	
@routes.get("/changes.html")
async def css(request):
	if globals.verbose: print('GET /changes.html')
	with open('templates/changes.html',encoding='utf8') as f:
		file=f.read().replace('{$globals.ver}',globals.ver).replace('{$changes}',''.join(globals.changes))
	return web.Response(text=file,status=200,headers={'content-type':'text/html'})
@routes.get("/changes.js")
async def js(request):
	if globals.verbose: print('GET /changes.js')
	with open('templates/changes.js',encoding='utf8') as f:
		file=f.read()
	return web.Response(text=file,status=200,headers={'content-type':'application/javascript'})
	
@routes.get("/lacket")
async def lacket(request):
	if globals.verbose: print('GET /lacket')
	with open('templates/lacket.html',encoding='utf8') as f:
		file=f.read().replace('{$globals.ver}',globals.ver)
	return web.Response(text=file,status=200,headers={'Access-Control-Allow-Origin':'https://merely.yiays.com','content-type':'text/html'})

@routes.get("/favicon.ico")
async def favicon(request):
	if globals.verbose: print('GET /favicon.ico')
	return web.Response(text='',status=404,headers={'content-type':'image/x-icon'})

app=web.Application()
app.add_routes(routes)
runner=web.AppRunner(app)

async def start():
	await runner.setup()
	site = web.TCPSite(runner,'0.0.0.0',globals.apiport)
	await site.start()
async def stop():
	await runner.cleanup()