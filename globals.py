import configparser

# objects waiting to be shared between modules
config=configparser.ConfigParser()
stats=False
meme=None
janitor=None
memedbpass=''
lockout={}
commandlist={'main':['reload']}
modules={'main':False,'reload':False}
bot=False
store='merely_data/'
dhelp={}
connected=False

verbose,logchannel,musicbuddy,feedbackchannel,modchannel,emurl,webserver,apiurl=(None,)*8
apiport,thonks,ver,lastver,changes,authusers,superusers,memechannels=(None,)*8

def reload():
	global verbose,logchannel,musicbuddy,feedbackchannel,modchannel,emurl,webserver,apiurl
	global apiport,thonks,ver,lastver,changes,lockout,authusers,superusers,memechannels
	
	print('reading config...')
	config.read(store+'config.ini')

	#settings
	verbose=config.getint('settings','verbose')
	logchannel=config.getint('settings','logchannel')
	musicbuddy=config.getint('settings','musicbuddy')
	feedbackchannel=config.getint('settings','feedbackchannel')
	modchannel=config.getint('settings','modchannel')
	emurl=config.get('settings','emurl')
	webserver=config.getboolean('settings','webserver')
	apiurl=config.get('settings','apiurl')
	apiport=config.getint('settings','apiport')

	#hmm
	thonks=config.get('settings','thonks')

	#versioning
	ver=config.get('settings','ver')
	lastver=config.get('settings','lastver')
	with open(store+'changes.md', 'r', encoding='utf-8') as file:
		changes=file.readlines()

	#perms
	lockout=config['lockout']

	authusers=[int(authuser) for authuser in config.get('settings','authusers').split(',')]
	superusers=[int(superuser) for superuser in config.get('settings','superusers').split(',')]
	
	memechannels={int(level):[int(channel) for channel in config.get('memechannels',level).split(',')] for level in config['memechannels']}
	print('config read!')

def save():
	global lockout,changes
	#perms
	for user,time in lockout.items():
		config.set('lockout',user,time)
	
	with open(store+'config.ini','w') as f:
		config.write(f)
	
	with open(store+'changes.md', 'w', encoding='utf-8') as file:
		file.writelines(changes)
	print('config saved!')

reload()
