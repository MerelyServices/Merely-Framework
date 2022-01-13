![merely logo](profile.png)
# merelybot
![Python build status](https://github.com/yiays/merely/workflows/merelybot/badge.svg?branch=master)

**merely is a framework for discord bots buit atop of nextcord**, merely is incredibly modular, multilingual, and supports live-reloading of extensions, translations, and config files! get started with the code on this repo, which provides a nice template config file and some example extensions that I use to make merely a useful bot on my own [discord server](https://discord.gg/wfKx24kDUR).

> *the web extension provides an API powering this website;*
> [visit the webUI >](https://merely.yiays.com/)

> *try out the flagship merelybot for yourself;*
> [add merely to your server >](https://discordapp.com/oauth2/authorize?client_id=309270899909984267&scope=bot&permissions=0)

## news
merely v1.0.0 has launched! with this update comes a wave of potential for 3rd party extensions and custom discord bots. it is also full of breaking changes, the config migration tool should be able to help, but .
> [see the roadmap for future updates >](https://github.com/yesiateyoursheep/merely/projects/1)

## changelog
you can read the up to date changelog [here](https://merely.yiays.com/changes.html).

## usage
 - clone the project to a folder
 - install python <=3.6
 - install required python packages with `python3 -m pip install -r requirements.txt`
 - create a discord bot in the [Discord Developer Portal](https://discordapp.com/developers/applications/), you will need the token to continue
 - give merely the token with
   - `export Merely="TOKEN"` on linux
   - `setx Merely "TOKEN"` on windows
   - *it's recommended you create a .bat or .sh file which assigns these variables whenever you start the bot*
   - *also note that the beta branch uses the 'MerelyBeta' environment variable instead*
 - run it with `python3 merelybot.py`
 - add your instance of merely to your server
 - *optional*: create a log channel on your server and copy the id to merely_data/config.ini > logchannel. - you can also do the same with a channel for feedback and a channel for moderators.

after the first run, you can enable commands by editing the file at merely_data/config.ini in order to enable extensions. simply switch the value of each extension you want from `False` to `True`, note that the meme extension is read-only for 3rd party developers.

once extensions have been enabled, you can list commands available to you using `m/help` in a discord channel the bot has access to.

## contributing
the best way to contribute is to create your own discord bot using this framework, and send any improvements to the framework my way in the form of a pull request!

### design
merely is a highly customizable and extensible discord bot. through the config file, people can create their own discord bots by enabling and disabling extensions, changing the bot name and prefix. other developers can even write their own extensions.

### code structure
extensions need to be able to be entirely independant of each other and should rarely need to communicate with each other. extensions must inherit from the [nextcord ext.commands.Cog](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#cogs) class. effort should be made to avoid clashes with existing commands, preferably by using subcommands. [extensions/example.py](extensions/example.py) should demonstrate all of this.

### file structure
extensions are placed in the extensions folder, from there, they will be added to the config and can be enabled.

## extensions
| extension | description | added |
| ------ | ----------- | ----- |
| [main](main.py)* | imports extensions, creates some global variables, establishes a log, and runs the main loop | 0.1.0 |
| [config](config.py)* | reads configuration data and ensures that the config file is valid | 1.0 |
| [help](extensions/help.py) | `help, about` - lists featured commands and can fetch docstrings on commands | 1.0 |
| [admin](extensions/admin.py) | `die, janitor, clean, purge` - power tools for server administrators | 1.0 |
| [greeter](extensions/greeter.py) | `welcome, farewell` - automated messages, configurable by admins | 1.0 |
| ------ | ----------- | ----- |
| [example](extensions/example.py) | `ping` - example commands for getting started on writing your own extension | 1.0 |

 - \* = must be imported for minimal functionality
