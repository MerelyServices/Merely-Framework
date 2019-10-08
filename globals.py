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
	'main':1,
	'config':1,
	'emformat':1,
}
bot=False
store='merely_data/'
dhelp={}
connected=False

owner=None
invite=None

verbose=False
logchannel=None
musicbuddy=None
feedbackchannel=None
modchannel=None
emurl='https://yiays.com/img/merely/em-'
apiurl='https://merely.yiays.com/'
apiport=8080
thonks=''
ver='0.0.0'
lastver='0.0.0'
authusers=''
superusers=''

memechannels={}
memesites={}

def reload():
	global modules,verbose,logchannel,musicbuddy,feedbackchannel,modchannel,emurl,apiurl
	global apiport,thonks,ver,lastver,changes,lockout,authusers,superusers,memechannels
	global memesites,owner,invite
	
	create = False
	
	print('reading config...')
	if not (os.path.exists(store+'config.ini') and os.path.isfile(store+'config.ini')):
		create = True
		print('[WARN] config doesn\'t exist at '+store+'config.ini, creating new config.ini with default settings...')
		with open(store+'config.ini','w', encoding='utf-8') as f:
			config.write(f)
	config.read(store+'config.ini')

	#owner
	owner=config.getint('owner','owner',fallback=None)
	invite=config.get('owner','invite',fallback=None)

	#modules
	modules.update({str(module):config.getint('modules',module,fallback=False) for module in config['modules']})

	#settings
	verbose=config.getint('settings','verbose',fallback=False)
	logchannel=config.getint('settings','logchannel',fallback=None)
	musicbuddy=config.getint('settings','musicbuddy',fallback=None)
	feedbackchannel=config.getint('settings','feedbackchannel',fallback=None)
	modchannel=config.getint('settings','modchannel',fallback=None)
	emurl=config.get('settings','emurl',fallback='https://yiays.com/img/merely/em-')
	apiurl=config.get('settings','apiurl',fallback='https://merely.yiays.com/')
	apiport=config.getint('settings','apiport',fallback=8080)

	#hmm
	thonks=config.get('settings','thonks',fallback='')

	#versioning
	ver=config.get('settings','ver',fallback='0.0.0')
	lastver=config.get('settings','lastver',fallback='0.0.0')
	
	if not (os.path.exists(store+'changes.md') and os.path.isfile(store+'changes.md')):
		create = True
		print('[WARN] config doesn\'t exist at '+store+'changes.md, creating new, empty, changes.md...')
		with open(store+'changes.md','w', encoding='utf-8') as f:
			f.write('')
		changes=''
	else:
		with open(store+'changes.md', 'r', encoding='utf-8') as file:
			changes=file.readlines()

	#perms
	lockout=config['lockout']

	authusers=[int(authuser) for authuser in config.get('settings','authusers',fallback='').split(',')]
	superusers=[int(superuser) for superuser in config.get('settings','superusers',fallback='').split(',')]
	
	memechannels={int(level):[int(channel) for channel in config.get('memechannels',level,fallback='').split(',')] for level in config['memechannels']}
	memesites={str(trust):[url for url in config.get('memesites',trust,fallback='').split(',')] for trust in config['memesites']}
	
	if create:
		with open(store+'config.ini','w', encoding='utf-8') as f:
			config.write(f)
	
	print('done!')

def save():
	global lockout,changes
	#perms
	for user,time in lockout.items():
		config.set('lockout',user,time)
	
	with open(store+'config.ini','w', encoding='utf-8') as f:
		config.write(f)
	
	with open(store+'changes.md', 'w', encoding='utf-8') as file:
		file.writelines(changes)
	print('config saved!')

reload()
