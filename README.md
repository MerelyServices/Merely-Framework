![merely logo](profile.png)
# merelybot
![Python build status](https://github.com/yiays/merely/workflows/merelybot/badge.svg?branch=master)

merely is a discord bot intended to be highly modular and able to enhance a [discord server](https://discord.gg/f6TnEJM) it's invited to with useful commands like...
 - `m/shorten` to shorten URLs | [demo](https://merely.yiays.com/#/shorten)
 - `m/vote` to hold live multichoice polls in a channel | [demo](https://merely.yiays.com/#/vote)
 - `m/welcome` and `m/farewell` to create custom messages when people leave or join | [demo](https://merely.yiays.com/#/welcome)
 - `m/clean` and `m/purge` to quickly clean up a text channel | [clean demo](https://merely.yiays.com/#/clean) | [purge demo](https://merely.yiays.com/#/purge)
 - `m/janitor` to make tidy channels where bot spam is automatically removed | [demo](https://merely.yiays.com/#/janitor)
 - `m/dice` to roll as many custom dice as your heart desires | [demo](https://merely.yiays.com/#/dice)
 - `m/meme` to bring the power of a [meme database](https://meme.yiays.com/) to a discord server | [demo](https://merely.yiays.com/#/meme)

in place of `m/`, you can also use `merely ` or `@merely `, eg `m/help`, `merely help` and `@merely help` are all valid.

> [visit the webUI >](https://merely.yiays.com/)

> [add merely to your server >](https://discordapp.com/oauth2/authorize?client_id=309270899909984267&scope=bot&permissions=0)

## rewrite
This rewrite intends to build merelybot from the ground up with *true* modularity as a primary goal.

## news
merely v1.0.0 has launched! with this update comes a wave of potential for 3rd party modules and custom discord bots.
> [see the roadmap for future updates >](https://github.com/yesiateyoursheep/merely/projects/1)

## changelog
you can read the up to date changelog [here](https://merely.yiays.com/changes.html) (or, alternatively, [here](merely_data/changes.md)).

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

after the first run, you can enable commands by editing the file at merely_data/config.ini in order to enable modules. simply switch the value of each module you want from `False` to `True`, note that the meme module has external dependencies and will not work in a local environment.

once modules have been enabled, you can list commands available to you using `m/help` in a discord channel the bot has access to.

## contributing
keeping the following design philosophy in mind, feel free to fix any bugs or add new features to a fork, and send me a pull request. you can also create modules independantly and keep them to yourself if you want.

### design
merely is a highly customizable and extensible discord bot. through the config file, people can create their own discord bots by enabling and disabling modules, changing the bot name and prefix. other developers can even write their own modules!

### code structure
modules need to be able to be entirely independant of each other and communicate to each other through the merelybot core module or globals. modules must inherit from the [discord.py ext.commands.Cog](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#cogs) class. effort should be made to avoid clashes with existing commands, preferably by using subcommands.

### file structure
modules are placed in the modules folder, from there, they will be added to the config and can be enabled.

## modules
| module | description | added |
| ------ | ----------- | ----- |
| [core](merelybot.py)* | imports all modules, creates some global variables, establishes a log, and runs the main loop | 0.1.0 |
| [config](globals.py)* | contains global variables and configuration data | 0.1.0 |
| [help](help.py)<sup>1</sup> | help contains help strings for all commands, lists of commands, lists of hints and other documentation. | 0.1.0 |
| [search](search.py) | google, google images and help search libraries/commands | 0.1.0 |
| [admin](admin.py) | commands restricted to mods and server owners | 0.1.0 |
| [censor](censor.py) | the blacklist, whitelist and algorithms used to determine if blacklisted words are in a string, also sass | 0.1.0 |
| [emformat](emformat.py)* | useful functions for formatting strings into discord embeds and vice versa | 0.1.0 |
| [fun](fun.py) | fun commands available to everyone, like `m/echo`, `m/vote` and `m/dice` | 0.1.0 |
| [meme](meme.py) | connects to [MemeDB](https://meme.yiays.com/) and provides commands and react buttons to interact with it. *legacy: stores and shares memes in a local database* | 0.1.0 |
| [webserver](webserver.py)<sup>1</sup> | serves [merely.yiays.com](https://merely.yiays.com/) | 0.2.0 |
| [stats](stats.py)<sup>1</sup> | statistics collection and storage, `m/stats` and [the stats page](https://merely.yiays.com/stats.html) | 0.2.0 |
| [obsolete](obsolete.py) | stores stubs for old obsolete commands and promotes merely music when someone attempts to use musicbot commands | 0.2.3 |
| [utils](utils.py) | provides useful general functions for programming merely | 0.7.3 |
| [tools](tools.py) | provides tools for all users (unlike admin, which is for mods and server owners) like `m/shorten` | 0.7.4 |
| [test](test.py) | a set of CI tests to help catch bugs early | 0.9.0 |
| [events](events.py) | a new events API for modules to use, allows for multiple modules to subscribe to the same events. | 1.0.0 |

 - \* = must be imported for minimal functionality
 - <sup>n</sup> = these modules are codependant - they must be enabled together
