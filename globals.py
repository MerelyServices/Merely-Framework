import os, time
from shutil import copy
import configparser

# objects waiting to be shared between modules
config=configparser.ConfigParser()

# defaults, should the ini file be missing or corrupted
lockout={}
modules={
	'core':True,
	'config':True,
	'emformat':True,
	'help':True,
	'admin':False,
	'censor':False,
	'fun':False,
	'meme':False,
	'obsolete':False,
	'search':False,
	'stats':False,
	'tools':False,
	'webserver':False
}
bot={}
store='merely_data/'
dhelp={}

owner=0
invite=None

prefix_short='m/'
prefix_long='merely'
name='merely'
verbose=True
beta=False
logchannel=0
musicbuddy=0
feedbackchannel=0
modchannel=0
emurl='https://yiays.com/img/merely/em-'
apiurl='https://merely.yiays.com/'
apiport=8080
iconurl="https://cdn.discordapp.com/avatars/309270899909984267/1d574f78b4d4acec14c1ef8290a543cb.png?size=64"
thonks=''
server='unknown'
ver='0.0.0'
lastver='0.0.0'
changes=[]
authusers=[]
superusers=[]
owneroptout=[]

memesources={}
memesubscriptions={}
memesites={'trusted':[],'blocked':[]}

class MemeChannel():
	def __init__(self, id : int, edge : int, tags = [], categories = []):
		self.id = id
		self.edge = edge
		self.tags = tags
		self.categories = categories

def reload():
	global modules,prefix_short,prefix_long,name,verbose,logchannel,musicbuddy,feedbackchannel,modchannel
	global emurl,apiurl,apiport,iconurl,thonks,server,ver,lastver,changes,lockout,authusers,superusers
	global memesources,memesubscriptions,memesites,owner,invite,beta,owneroptout
	
	print('reading config...')
	assurepath(store+'config.ini')
	config.read(store+'config.ini')

	#owner
	owner=config.getint('owner','owner',fallback=owner)
	invite=config.get('owner','invite',fallback=invite)

	#modules
	if assuresection('modules',modules):
		modules = {str(module):config.getboolean('modules',module,fallback=False) for module in config['modules']}

	#settings
	assuresection('settings',{
		'prefix_short':prefix_short,
		'prefix_long':prefix_long,
		'name':name,
		'verbose':verbose,
		'beta':beta,
		'logchannel':logchannel,
		'musicbuddy':musicbuddy,
		'feedbackchannel':feedbackchannel,
		'modchannel':modchannel,
		'emurl':emurl,
		'apiurl':apiurl,
		'apiport':apiport,
		'iconurl':iconurl,
		'thonks':thonks,
		'server':server,
		'ver':ver,
		'lastver':lastver,
		'authusers':','.join([str(u) for u in authusers]),
		'superusers':','.join([str(u) for u in superusers])
	})
	prefix_short=config.get('settings','prefix_short',fallback=prefix_short).replace(' ','')
	prefix_long=config.get('settings','prefix_long',fallback=prefix_long).replace(' ','')
	name=config.get('settings','name',fallback=name)
	verbose=config.getboolean('settings','verbose',fallback=verbose)
	beta=config.getboolean('settings','beta',fallback=beta)
	logchannel=config.getint('settings','logchannel',fallback=logchannel)
	musicbuddy=config.getint('settings','musicbuddy',fallback=musicbuddy)
	feedbackchannel=config.getint('settings','feedbackchannel',fallback=feedbackchannel)
	modchannel=config.getint('settings','modchannel',fallback=modchannel)
	emurl=config.get('settings','emurl',fallback=emurl)
	apiurl=config.get('settings','apiurl',fallback=apiurl)
	apiport=config.getint('settings','apiport',fallback=apiport)

	#hmm
	thonks=config.get('settings','thonks',fallback=thonks)

	#server info for stats
	server=config.get('settings','server',fallback=server)

	#versioning
	ver=config.get('settings','ver',fallback=ver)
	lastver=config.get('settings','lastver',fallback=lastver)
	
	if assurepath(store+'changes.md'):
		changes=''
	else:
		with open(store+'changes.md', 'r', encoding='utf-8') as file:
			changes=file.readlines()

	#perms
	assuresection('lockout',{})
	lockout=config['lockout']

	authusers = failsafelist(config.get('settings','authusers',fallback='').split(','), int)
	superusers = failsafelist(config.get('settings','authusers',fallback='').split(','), int)
	owneroptout = failsafelist(config.get('settings','owneroptout',fallback='').split(','), int)
	
	assuresection('memesources',{})
	for channel in config['memesources']:
		memesources[int(channel)] = config.get('memesources', channel, fallback='')
	assuresection('memesubscriptions',{})
	for channel in config['memesubscriptions']:
		memesubscriptions[int(channel)] = config.get('memesubscriptions', channel, fallback='')
	
	assuresection('memesites',{'trusted':'','blocked':''})
	memesites={trust:[url for url in config.get('memesites',trust,fallback='').split(',')] for trust in config['memesites']}
	
	assuresection('janitor',{'strict':'','relaxed':''})

	# make a backup of the config file before saving
	if not os.path.exists(store+'config_history/'+time.strftime("%m-%y")):
		os.makedirs(store+'config_history/'+time.strftime("%m-%y"))
	copy('config.ini', 'config_history/'+time.strftime("%m-%y")+'/config-'+time.strftime("%H:%M.%S-%d-%m-%y")+'.ini')
	with open(store+'config.ini','w', encoding='utf-8') as f:
		config.write(f)
	
	#regenerate missing files
	assurepath(store+'blacklist.txt')
	assurepath(store+'whitelist.txt')
	assurepath(store+'uptime.txt')
	assurepath(store+'playing.txt')
	assurepath(store+'alive.txt')
	
	print('done!')

def save():
	global lockout,changes,owneroptout,memesources,memesubscriptions
	#perms
	for user,time in lockout.items():
		config.set('lockout',user,time)
	
	config.set('settings','owneroptout',','.join([str(a) for a in owneroptout]))
	config.set('memesites','trusted',','.join([str(a) for a in memesites['trusted']]))
	config.set('memesites','blocked',','.join([str(a) for a in memesites['blocked']]))
	
	for channel in memesources:
		config.set('memesources', str(channel), memesources[channel])
	for channel in memesubscriptions:
		config.set('memesubscriptions', str(channel), memesubscriptions[channel])
	
	with open(store+'config.ini','w', encoding='utf-8') as f:
		config.write(f)
	
	with open(store+'changes.md', 'w', encoding='utf-8') as file:
		file.writelines(changes)
	print('config saved!')

def assurepath(path):
	if not (os.path.exists(path) and os.path.isfile(path)):
		print('[WARN] config doesn\'t exist at '+path+', creating new, empty, '+path+'...')
		with open(path,'w', encoding='utf-8') as f:
			f.write('')
		return True
	return False

def assuresection(section,default):
	if config.has_section(section):
		for key, defaultvalue in default.items():
			if not key in config[section]:
				config.set(section, key, defaultvalue)
		return True
	else:
		config[section]={str(a):str(b) for a,b in default.items()}

def failsafelist(_list, _type):
	out = []
	for x in _list:
		try:
			out.append((_type)(x))
		except ValueError:
			continue
	return out

reload()
