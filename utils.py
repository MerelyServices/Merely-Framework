timedividers = {
	300 : [60,'minute'],
	7200 : [3600,'hour'],
	172800 : [86400,'day'],
	2592000 : [2592000,'month'],
	31104000 : [31104000,'year'],
	311040000 : [311040000,'decade'],
	3110400000 : [3110300000,'century','centuries'],
	31104000000 : [31103000000,'millenia','millenia'],
	31104000000000000 : [31104000000000000,'eon','eons']
}

def time_fold(s:int):
	for m,a in sorted(timedividers.items(),reverse=True):
		if s>m:
			ns = round(s/a[0])
			return str(ns)+' '+(a[1] if ns==1 else (a[2] if len(a)>2 else a[1]+'s'))
	return str(s)+' second'+('s' if s!=1 else '')
