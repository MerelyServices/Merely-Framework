import re
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
	timedivider(threshold=300, divider=60, unit='minute'),
	timedivider(threshold=0, divider=1, unit='second')
]

def time_fold(s:int):
	output = ''
	n = s
	for td in timedividers:
		if s > td.threshold:
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

# TODO: create string stripper function for meme search and censor