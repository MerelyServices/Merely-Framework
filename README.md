![merely logo](profile.png)
# merelybot
[![Python build status](https://github.com/MerelyServices/Merely-Framework/actions/workflows/pythonapp.yml/badge.svg)](https://github.com/MerelyServices/Merely-Framework/actions/workflows/pythonapp.yml)

**merely is a framework for discord bots buit atop of disnake**, merely is incredibly modular, multilingual, and supports live-reloading of extensions, translations, and config files! get started with the code on this repo, which provides a nice template config file and some example extensions.

> demo an implementation of merelybot, merely, on my [discord server](https://discord.gg/wfKx24kDUR)

> *try out the flagship merelybot for yourself;*
> [add merely to your server >](https://discord.com/oauth2/authorize?client_id=309270899909984267&permissions=0&scope=bot%20applications.commands)

## news
translation tooling for my projects (including merely) has launched! contribute translations with the help of this tooling and see your language become available in all sorts of places!
> [try it now >](https://translate.yiays.com)

merely v1.0.0 has launched! with this update comes a wave of potential for 3rd party extensions and custom discord bots. it is also full of breaking changes. upgrading requires manual migration of your config.
> [see the roadmap for future updates >](https://github.com/MerelyServices/Merely-Framework/projects/1)

## usage
 - clone the project to a folder
 - install python <=3.9
 - install required python packages with `python3 -m pip install -r requirements.txt`
 - create a discord bot in the [Discord Developer Portal](https://discordapp.com/developers/applications/), you will need the token to continue
 - give merelybot the token by setting it in the [main] section of the config.
 - Add your user ID to the superusers section of the [auth] section of the config.
 - run it with `python3 main.py`
 - add your merelybot to your server.
 - enable and disable extensions as you please using `m/module`.

`m/help` will list some featured commands, if they have a ❌ symbol, they require an extension to be enabled.

## contributing
the best way to contribute is to create your own discord bot using this framework, and send any improvements to the framework my way in the form of a pull request!

### design
merely is a highly customizable and extensible discord bot. through the config file, people can create their own discord bots by enabling and disabling extensions, changing the bot name and prefix. other developers can even write their own extensions.

### code structure
extensions need to be able to be entirely independant of each other and should rarely need to communicate with each other. extensions must inherit from the [disnake.ext.commands.Cog](https://docs.disnake.dev/en/latest/ext/commands/api.html#cog) class. effort should be made to avoid clashes with existing commands, preferably by using subcommands. [extensions/example.py](extensions/example.py) should demonstrate all of this.

### file structure
extensions are placed in the extensions folder. from there, they will be added to the config and can be enabled.

## extensions
| extension | description | added |
| ------ | ----------- | ----- |
| [main](main.py)* | imports extensions, creates some global variables, establishes a log, and runs the main loop | 0.1.0 |
| [config](config.py)* | reads configuration data and ensures that the config file is valid | 1.0 |
| [babel](babel.py)* | provides translated and formatted strings that contributors can easily translate to more languages | 1.0 |
| [auth](extensions/__auth.py)* | provides security checks for other commands which need authorization | 1.0 |
| [error](extensions/error.py) | provides error handling for all other extensions so they don't have to | 1.0 |
| [log](extensions/log.py) | provides logging to a designated channel on a server for convenience | 1.0 |
| [help](extensions/help.py)** | `help, about` - lists featured commands and can fetch docstrings on commands | 1.0 |
| [language](extensions/language.py) | `language` - allows bot users to change the language or request a translation | 1.0 |
| [admin](extensions/admin.py) | `die, janitor, clean, purge` - power tools for server administrators | 1.0 |
| [dice](extensions/dice.py) | `dice` - a simple dice rolling command with some advanced features | 1.0 |
| [emoji](extensions/emoji.py) | `emoji, thonk` - allows non-nitro users to use a selection of custom emojis | 1.0 |
| [greeter](extensions/greeter.py) | `welcome, farewell` - automated messages, configurable by admins | 1.0 |
| [meme](extensions/meme.py) | a stand-in extension for promoting a different bot | 1.0 |
| [music](extensions/music.py) | a stand-in extension for promoting a different bot | 1.0 |
| [poll](extensions/poll.py) | `poll` - adds polls to discord with an interactive poll builder and countdown timers | 1.0 |
| [reactroles](extensions/reactroles.py) | `reactrole` - adds reaction roles to discord with an interactive setup | 1.0 |
| [prefix](extensions/prefix.py) | `prefix` - allows guilds to have a custom prefix to use when this bot | 1.0 |
| [premium](extensions/premium.py) | `premium` - locks select features behind a paywall, using a premium role to check | 1.0 |
| ------ | ----------- | ----- |
| [example](extensions/example.py) | `ping` - example commands for getting started on writing your own extension | 1.0 |
| [lightbulb](extensions/lightbulb.py) | an experimental extension for commandless bot interaction | 1.0 |

 - \* = must be imported for minimal functionality
 - \*\* = must be imported, or replaced with a compatible replacement