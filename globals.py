import configparser

# objects waiting to be shared between modules
config=configparser.ConfigParser()
stats=False
meme=None
lockout={}
commandlist={'main':['reload']}
modules={'main':False,'reload':False}
bot=False
store='merely_data/'
dhelp={}
connected=False

memechannels={
	0:[238976460063244288],
	1:[360218645823094794],
	2:[556933225985867857],
	3:[563899031684775945]
}

verbose,logchannel,feedbackchannel,modchannel,emurl,webserver,apiurl,apiport=(0,)*8
thonks,ver,lastver,changes,authusers,superusers=(0,)*6

def reload():
	global verbose,logchannel,feedbackchannel,modchannel,emurl,webserver,apiurl,apiport
	global thonks,ver,lastver,changes,lockout,authusers,superusers
	
	print('reading config...')
	config.read(store+'config.ini')

	#settings
	verbose=config.getint('settings','verbose')
	logchannel=config.getint('settings','logchannel')
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
	with open(store+'changes.txt', 'r', encoding='utf-8') as file:
		changes=file.readlines()

	#perms
	lockout=config['lockout']

	authusers=[int(authuser) for authuser in config.get('settings','authusers').split(',')]
	superusers=[int(superuser) for superuser in config.get('settings','superusers').split(',')]
	print('config read!')

def save():
	global lockout
	#perms
	for user,time in lockout.items():
		config.set('lockout',user,time)
	
	with open(store+'config.ini','w') as f:
		config.write(f)
	print('config saved!')

reload()
