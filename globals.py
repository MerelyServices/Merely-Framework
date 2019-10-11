import os
import configparser

# objects waiting to be shared between modules
config=configparser.ConfigParser()
stats=None
meme=None
janitor=None
memedbpass=''
lockout={}
commandlist={'config':['reload']}
modules={
	'main':True,
	'config':True,
	'emformat':True,
	'reload':False,
	'admin':False,
	'censor':False,
	'fun':False,
	'help':False,
	'meme':False,
	'obsolete':False,
	'search':False,
	'stats':False,
	'webserver':False
}
bot=False
store='merely_data/'
dhelp={}
connected=False

owner=0
invite=None

verbose=True
beta=False
logchannel=0
musicbuddy=0
feedbackchannel=0
modchannel=0
emurl='https://yiays.com/img/merely/em-'
apiurl='https://merely.yiays.com/'
apiport=8080
thonks=''
ver='0.0.0'
lastver='0.0.0'
authusers=[]
superusers=[]
owneroptout=[]

memechannels={0:[],1:[],2:[],3:[]}
memesites={'trusted':[],'blocked':[]}

def reload():
	global modules,verbose,logchannel,musicbuddy,feedbackchannel,modchannel,emurl,apiurl
	global apiport,thonks,ver,lastver,changes,lockout,authusers,superusers,memechannels
	global memesites,owner,invite,beta,owneroptout
	
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
		'verbose':verbose,
		'beta':beta,
		'logchannel':logchannel,
		'musicbuddy':musicbuddy,
		'feedbackchannel':feedbackchannel,
		'modchannel':modchannel,
		'emurl':emurl,
		'apiurl':apiurl,
		'apiport':apiport,
		'thonks':thonks,
		'ver':ver,
		'lastver':lastver
	})
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
	
	assuresection('memechannels',{'0':'','1':'','2':'','3':''})
	for level in config['memechannels']:
		for channel in config.get('memechannels',level,fallback='').split(','):
			try:
				memechannels[int(level)].append(int(channel))
			except ValueError:
				continue
	
	assuresection('memesites',{'trusted':'','blocked':''})
	memesites={trust:[url for url in config.get('memesites',trust,fallback='').split(',')] for trust in config['memesites']}
	
	#regenerate missing files
	assuresection('janitor',{'strict':'','relaxed':''})
	with open(store+'config.ini','w', encoding='utf-8') as f:
		config.write(f)
	assurepath(store+'blacklist.txt')
	assurepath(store+'whitelist.txt')
	assurepath(store+'uptime.txt')
	assurepath(store+'playing.txt')
	assurepath(store+'alive.txt')
	
	print('done!')

def save():
	global lockout,changes,owneroptout
	#perms
	for user,time in lockout.items():
		config.set('lockout',user,time)
	
	config.set('settings','owneroptout',','.join([str(a) for a in owneroptout]))
	config.set('memesites','trusted',','.join([str(a) for a in memesites['trusted']]))
	config.set('memesites','blocked',','.join([str(a) for a in memesites['blocked']]))
	
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
