import time, psutil, asyncio
import globals, emformat
from discord import __version__ as discordversion
from discord.ext import commands,tasks

# ['stats']=['stats']

class Stats(commands.Cog):
	def __init__(self,bot):
		self.bot=bot
		
		self.status='online'
		self.exposure="populating..."
		self.responses="0/0 messages responded to since last reboot."
		self.sentcount=0
		self.recievedcount=0
		self.starttime=time.time()
		self.uptime="calculating..."
		self.d=self.h=self.m=self.s=0
		self.modules='populating...'
		self.library="discord.py v"+discordversion
		self.core="merelybot v"+globals.ver
		self.memes="unavailable"
		self.cpu_usage='0%'
		self.ram_usage='0MB/0MB (0%)'
		self.hardware='merely is running on a custom windows server.'
		self.gentime='please wait...'
		self.lastuptime=0
		
		self.inituptime()
		self.runstats.start()
	
	def cog_unload(self):
		self.runstats.cancel()
	
	@commands.command(pass_context=True, no_pm=False, aliases=['status','ver','version'])
	async def stats(self,ctx):
		if globals.verbose:print('stats command')
		await emformat.make_embed(ctx.message.channel,'for constantly updating stats, go to '+globals.apiurl+'stats.html',
		'merely stats','',color=0x2C5ECA,thumbnail=globals.emurl+'greet.gif',
		fields={
			'exposure': self.exposure,
			'responses': self.responses,
			'uptime': self.uptime,
			'modules': self.modules,
			'library': self.library,
			'core': self.core,
			#'memes': self.memes,
			'cpu usage': self.cpu_usage,
			'ram usage': self.ram_usage,
			'hardware': self.hardware,
			'generated time': self.gentime
		},
		icon=globals.iconurl,footer="merely v"+globals.ver+" - created by Yiays#5930",link=globals.apiurl)

	def inituptime(self):
		with open(globals.store+'uptime.txt','r') as f:
			line=f.readline() #get starting point
			savelines=[]
			self.upmins=0
			self.downmins=0
			i=0
			sprint=0
			for line in f.readlines():
				ii=[int(x) for x in line.split('-')]
				if ii[0]>i+2:
					self.upmins+=i-sprint
					self.downmins+=ii[0]-i
					savelines.append(str(sprint)+'-'+str(i))
					sprint=ii[0]
				i=ii[-1]
			savelines.append(str(sprint)+'-'+str(i))
		with open(globals.store+'uptime.txt','w') as f:
			for line in savelines:
				f.write(line+'\n')

	@tasks.loop(seconds=1.0)
	async def runstats(self):
		try:
			if round(time.time())%60==0 and round(time.time()/60)!=self.lastuptime:
				self.lastuptime=round(time.time()/60)
				with open(globals.store+'uptime.txt','a') as f:
					f.write(str(round(time.time()/60)-26394323)+'\n')
				self.upmins+=1
			
			self.m, self.s = divmod(time.time()-self.starttime, 60)
			self.h, self.m = divmod(self.m, 60)
			self.d, self.h = divmod(self.h, 24)
			
			self.exposure="**"+str(len(self.bot.guilds))+"** servers."
			self.responses=str(self.sentcount)+"/"+str(self.recievedcount)+" messages responded to since last reboot."
			self.modules=', '.join(list(globals.modules.keys()))
			self.uptime=str(round((self.upmins*100)/max(self.upmins+self.downmins,1),2))+'%'
			self.cpu_usage=str(psutil.cpu_percent())+'%'
			self.ram_usage=str(round(psutil.virtual_memory().used/1000000))+'MB ('+str(round((psutil.virtual_memory().used*100)/psutil.virtual_memory().total))+'%)'
			self.gentime=time.asctime(time.localtime())+'+1300'
		except Exception as e:
			print(repr(e))