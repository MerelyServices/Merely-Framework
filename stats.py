import time, psutil, asyncio
import globals, emformat
from discord import __version__ as discordversion
from discord.ext import commands

class Stats(commands.Cog):
	def __init__(self):
		self.status='online'
		self.exposure="populating..."
		self.responses="0/0 messages responded to since last reboot."
		self.sentcount=0
		self.recievedcount=0
		self.memecount=0
		self.starttime=time.time()
		self.uptime="calculating..."
		self.d=self.h=self.m=self.s=0
		self.modules='populating...'
		self.library="discord.py v"+discordversion
		self.core="merelybot v"+globals.ver
		self.memes="calculating..."
		self.cpu_usage='0%'
		self.ram_usage='0MB/0MB (0%)'
		self.hardware='merely is running on a custom windows server.'
		self.gentime='please wait...'
		self.lastuptime=0
	
	@commands.command(pass_context=True, no_pm=False, aliases=['status','ver','version'])
	async def stats(self,ctx):
		if globals.verbose:print('stats command')
		await emformat.make_embed(ctx.message.channel,'for constantly updating stats, go to '+globals.apiurl+'.',
		'merely stats','',0x2C5ECA,'',globals.emurl+'greet.gif',
		{
			'exposure': globals.stats.exposure,
			'responses': globals.stats.responses,
			'uptime': globals.stats.uptime,
			'modules': globals.stats.modules,
			'library': globals.stats.library,
			'core': globals.stats.core,
			'memes': globals.stats.memes,
			'cpu usage': globals.stats.cpu_usage,
			'ram usage': globals.stats.ram_usage,
			'hardware': globals.stats.hardware,
			'generated time': globals.stats.gentime
		},
		'','',globals.apiurl)

	async def runstats(self):
		while True:
			start=time.perf_counter()
			if round(time.time())%60==0 and round(time.time())/60!=self.lastuptime:
				self.lastuptime=round(time.time())/60
				with open(globals.store+'uptime.txt','a+') as f:
					f.write(str(round(time.time()/60))+'\n')
					f.seek(0)
					i=int(f.readline())
					uptime=0
					downtime=0
					lines=f.readlines()
					for line in lines:
						line=int(line)
						if i+1==line:
							uptime+=1
						else:
							downtime+=line-i
						i=line
					self.uptime=str(round((uptime*100)/max(uptime+downtime,1),2))+'%'
			
			with open(globals.store+'memes.txt','r',encoding='utf8') as f:
				self.memecount=len(f.readlines())
			self.m, self.s = divmod(time.time()-self.starttime, 60)
			self.h, self.m = divmod(self.m, 60)
			self.d, self.h = divmod(self.h, 24)
			
			self.exposure="**"+str(len(globals.bot.guilds))+"** servers with **"+str(sum([len(s.members) for s in globals.bot.guilds]))+"** members."
			self.responses=str(self.sentcount)+"/"+str(self.recievedcount)+" messages responded to since last reboot."
			self.modules=', '.join(list(globals.modules.keys()))
			self.memes=str(self.memecount)
			self.cpu_usage=str(psutil.cpu_percent())+'%'
			self.ram_usage=str(round(psutil.virtual_memory().used/1000000))+'MB ('+str(round((psutil.virtual_memory().used*100)/psutil.virtual_memory().total))+'%)'
			self.gentime=time.asctime(time.localtime())+'+1300'
			
			await asyncio.sleep(1-(start-time.perf_counter()))