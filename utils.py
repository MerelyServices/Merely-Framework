import re
import time
from collections import namedtuple

timedivider = namedtuple('timedivider', ['threshold', 'divider', 'unit', 'unitplural'], defaults=[0, 0, 'null', None])

timedividers = [
	timedivider(threshold=31104000000000000, divider=31104000000000000, unit='eon', unitplural='eons'),
	timedivider(threshold=31104000000, divider=31103000000, unit='millenia', unitplural='millenia'),
	timedivider(threshold=311040000, divider=311040000, unit='decade'),
	timedivider(threshold=31104000, divider=31104000, unit='year'),
	timedivider(threshold=2592000, divider=2592000, unit='month'),
	timedivider(threshold=172800, divider=86400, unit='day'),
	timedivider(threshold=7200, divider=3600, unit='hour'),
	timedivider(threshold=60, divider=60, unit='minute'),
	timedivider(threshold=0, divider=1, unit='second')
]

def time_fold(s:int):
	output = ''
	n = s
	for td in timedividers:
		if s >= td.threshold:
			# divide by the divider and return the remainder
			ns, n = divmod(n, td.divider)
			ns = int(ns)
			
			if ns == 1:
				plural = td.unit
			else:
				plural = f"{td.unit}s" if td.unitplural == None else td.unitplural
			
			output += f"{ns} {plural}, "
	return output[:-2]

def FindURLs(string):
	urls = re.findall(r'(http[s]?:\/\/[A-z0-9/?.&%;:\-=@]+)', string)
	return urls

def SanitizeMessage(msg):
	result = msg.content
	
	# Replace mentions with username#discrim
	for mention in msg.mentions:
		# Both <@USER_ID> and <@!USER_ID> are valid for some reason
		result = result.replace("<@!"+str(mention.id)+">", '@' + mention.name + '#' + str(mention.discriminator)).replace("<@"+str(mention.id)+">", '@' + mention.name + '#' + str(mention.discriminator))
	
	# Replace channel mentions with role name
	for mention in msg.channel_mentions:
		result = result.replace("<#"+str(mention.id)+">", '#'+mention.name)
	
	# Replace role mentions with role name
	for mention in msg.role_mentions:
		result = result.replace("<@&"+str(mention.id)+">", '@'+mention.name)
	
	# Remove links from message
	result = result.replace("https://", "").replace("http://", "")
	
	return result

class Cached():
	""" Cached variable datatype, use Cached.old to determine if data needs refreshing """
	def __init__(self, data=None, age=0, threshold=300):
		self.data = data
		self.threshold = threshold
		self.age = age
		self.refresh = False
	
	@property
	def data(self):
		return self.__data
	@data.setter
	def data(self, data):
		self.__data = data
		self.age = int(time.time())
	
	@property
	def old(self):
		if self.refresh:
			self.refresh = False
			return True
		return self.age < int(time.time())-self.threshold

# TODO: create string stripper function for meme search and censor