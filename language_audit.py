"""
  Example - Simple extension for Merely Framework
"""

import os, re
from glob import glob
from main import MerelyBot

# regex
SCOPEFINDER = re.compile(r"SCOPE = '([0-9a-z]+)'")
BABEL_INTERNAL = re.compile(r"self\([^,]+,\s?'([0-9a-z_]+)',\s?'([0-9a-z_]+)'")
BABEL_GLOBAL = re.compile(r"babel\([^,]+,\s?'([0-9a-z_]+)',\s?'([0-9a-z_]+)'")
BABEL_LOCAL = re.compile(r"babel\([^,]+,\s?'([0-9a-z_]+)'")
SETTING_LOCAL = (
  re.compile(r"(?:Toggleable|Listable|Selectable|Stringable)\([^,]+,\s[^,]+,\s'([a-z_]+)'")
)
COMMENT_OVERRIDE = re.compile(r"#BABEL: ([0-9a-z_,#-]+)\n")


def main(lang=None):
  """ Fire and forget language auditing """
  # Create bot but don't connect
  bot = MerelyBot(loadall=True, quiet=True)

  if lang is None:
    lang = bot.babel.defaultlang

  print("\nStarting language audit...")

  files = ['auth.py']
  files += glob(os.path.join('extensions', '*.py'))
  files += glob(os.path.join('overlay', 'extensions', '*.py')) if bot.overlay else []

  filecontent:dict[str, str] = {}
  found_scopekeys:set[str] = set()
  special_scopekeys:dict[str, set[str]] = {'wildcard': set(), 'ignore': set()}
  cmp_scopekeys:set[str] = bot.babel.scope_key_pairs(lang)

  found_stats:dict[str, int] = {
    'babel_internal': 0, 'babel_global': 0, 'babel_local': 0, 'setting': 0, 'comment': 0
  }

  for file in files:
    with open(file, 'r', encoding='utf-8') as module:
      content = '\n'.join(module.readlines())
      scope = ''
      if match := SCOPEFINDER.search(content):
        scope = match[1]
      if scope not in filecontent:
        filecontent[scope] = content
      else:
        filecontent[scope] += '\n' + content

  with open('babel.py', 'r', encoding='utf-8') as module:
    content = '\n'.join(module.readlines())
    for match in BABEL_INTERNAL.findall(content):
      found_stats['babel_internal'] += 1
      found_scopekeys.add(f'{match[0]}/{match[1]}')

  for scope in filecontent:
    filebuffer = filecontent[scope]
    for match in BABEL_GLOBAL.findall(filebuffer):
      found_stats['babel_global'] += 1
      found_scopekeys.add(f'{match[0]}/{match[1]}')
      filebuffer = re.sub(BABEL_GLOBAL, '', filebuffer, 1)
    if scope:
      for match in BABEL_LOCAL.findall(filebuffer):
        found_stats['babel_local'] += 1
        if scope == 'system' and match.startswith('extension'):
          # Exemption for legacy strings
          found_scopekeys.add(f'main/{match}')
        else:
          found_scopekeys.add(f'{scope}/{match}')
        filebuffer = re.sub(BABEL_LOCAL, '', filebuffer, 1)
      for match in SETTING_LOCAL.findall(filebuffer):
        found_stats['setting'] += 1
        found_scopekeys.add(f'{scope}/{match}')
        filebuffer = re.sub(SETTING_LOCAL, '', filebuffer, 1)
    for match in COMMENT_OVERRIDE.findall(filebuffer):
      found_stats['comment'] += 1
      for submatch in match.split(','):
        if '/' in submatch:
          key = submatch
        elif scope:
          key = f'{scope}/{submatch}'
        if '#' in key:
          special_scopekeys['wildcard'].add(key)
        elif '-' in key:
          special_scopekeys['ignore'].add(key.replace('-', ''))
        else:
          found_scopekeys.add(key)
      filebuffer = re.sub(COMMENT_OVERRIDE, '', filebuffer, 1)

  for cmd in bot.slash_commands:
    docname = f'command_{cmd.body.name.split()[0]}_help'
    for entry in cmp_scopekeys:
      if entry.endswith(docname):
        found_scopekeys.add(entry)
        break
    else:
      if hasattr(cmd.cog, 'SCOPE'):
        found_scopekeys.add(f'{cmd.cog.SCOPE}/{docname}')

  for key in special_scopekeys['wildcard']:
    for i in range(0,9):
      reskey = key.replace('#', str(i))
      if reskey in cmp_scopekeys:
        found_scopekeys.add(reskey)
      elif i > 0:
        break

  found_scopekeys = found_scopekeys.difference(special_scopekeys['ignore'])

  unmapped = found_scopekeys.difference(cmp_scopekeys)
  unused = cmp_scopekeys.difference(found_scopekeys)

  print("\nSTATS\n==========")
  print('\n'.join(f'{k}: {v}' for k,v in found_stats.items()))
  print("\nUNMAPPED\n==========")
  print('\n'.join(unmapped))
  print("\nUNUSED\n==========")
  print('\n'.join(unused))

  print(f"\nFinished language audit, unmapped: {len(unmapped)}, unused: {len(unused)}")


if __name__ == '__main__':
  main()
