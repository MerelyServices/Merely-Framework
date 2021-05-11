from configparser import ConfigParser
import discord
from discord.ext import commands
import os

class Babel():
    path = 'babel/'
    langs = {}

    def __init__(self, config:ConfigParser):
        self.config = config
        self.baselang = config.get('language', 'default', fallback='en')

        if os.path.isfile(self.path):
            os.remove(self.path)
        if not os.path.exists(self.path) or not os.path.exists(self.path+self.baselang+'.ini'):
            raise Exception(f"The path {self.path} must exist and contain a complete {self.baselang}.ini.")
        
        for langfile in os.scandir(self.path):
            langfile = langfile.name
            if langfile[-4:] == '.ini':
                langname = langfile[:-4]
                self.langs[langname] = ConfigParser(comment_prefixes='@', allow_no_value=True) # create a configparser that should preserve comments
                self.langs[langname].read(self.path+langfile)
                if 'meta' not in self.langs[langname]:
                    self.langs[langname].add_section('meta')
                self.langs[langname].set('meta', 'language', langname)
                with open(self.path+langfile, 'w', encoding='utf-8') as f:
                    self.langs[langname].write(f)

    def __call__(self, ctx:commands.Context, scope:str, key:str, **values):
        reqlangs = []
        
        if str(ctx.author.id) in self.config['language']:
            nl = self.config.get('lang', str(ctx.author.id))
            reqlangs.append(nl)
            if len(nl) > 2: reqlangs.append(nl[:2])
        if str(ctx.guild.id) in self.config['language']:
            nl = self.config.get('lang', str(ctx.guild.id))
            reqlangs.append(nl)
            if len(nl) > 2: reqlangs.append(nl[:2])
        reqlangs.append(self.baselang)

        match = None
        for reqlang in reqlangs:
            if reqlang in self.langs.keys():
                if scope in self.langs[reqlang]:
                    if key in self.langs[reqlang][scope]:
                        if len(self.langs[reqlang][scope][key]) > 0:
                            match = self.langs[reqlang][scope][key]
                            break

        if match is None:
            return "{MISSING STRING}"
        
        # Fill in values in the string
        for k,v in values.items():
            match=match.replace('{'+k+'}', v)

        return match