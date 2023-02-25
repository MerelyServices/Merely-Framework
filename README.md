![Merely logo](profile.png)
# Merelybot
![Python build status](https://github.com/yiays/merely/workflows/merelybot/badge.svg?branch=master)
**Merelybot is an extended feature-set for python Discord bots. Adding features like live reloading of code, a feature rich help command, translation support, error handling, and paywalled commands.**

## Featured implementations
You can test these implementations on my [official Discord server](https://discord.gg/wfKx24kDUR).
 - [Merely](https://discordapp.com/oauth2/authorize?client_id=309270899909984267&scope=bot&permissions=0) is an example implementation of the framework. Merely uses the default config included with this code so you can run it yourself.
 - [ConfessionBot](https://github.com/yiays/ConfessionBot-2.0) is an anonymous messaging system for Discord. ConfessionBot uses the help command, translation support, and module reloading features to speed up development and shares improvements to the framework back here.

## News
Translation tooling for my projects (including MerelyBot) has launched! contribute translations with the help of this tooling and see your language become available in all sorts of places!
> [try it now >](https://translate.yiays.com)

merely v1.0.0 has launched! with this update comes a wave of potential for 3rd party extensions and custom discord bots. it is also full of breaking changes, the config migration tool should be able to help, but .
> [see the roadmap for future updates >](https://github.com/yesiateyoursheep/merely/projects/1)

## Usage
 - Clone the project to a folder
 - Install python <=3.9
 - Install required python packages with `python3 -m pip install -r requirements.txt`
 - Create a discord bot in the [Discord Developer Portal](https://discordapp.com/developers/applications/), you will need the token to continue
 - Give MerelyBot the token by setting it in the [main] section of the config
 - Run MerelyBot with `python3 merelybot.py`
 - Add your instance of merely to your server
 - *optional*: create a log channel on your server and copy the id to merely_data/config.ini > logchannel. - you can also do the same with a channel for feedback and a channel for moderators.

The first run generates a `config.ini` file, you can modify it from there to enable features.

## Contributing
The best way to contribute is to create your own discord bot using this framework, and send any improvements to the framework my way in the form of a pull request!

### Design
Merely is a highly customizable and extensible discord bot. through the config file, people can create their own discord bots by enabling and disabling extensions, and changing the bot name. Other developers can even write their own extensions.

### Code structure
Extensions need to be able to be entirely independant of each other and should rarely need to communicate with each other. extensions must inherit from the [disnake.ext.commands.Cog](https://docs.disnake.dev/en/latest/ext/commands/api.html#cog) class. effort should be made to avoid clashes with existing commands, preferably by using subcommands. [extensions/example.py](extensions/example.py) should demonstrate all of this.

### File structure
 - Core plugins are stored in the top directory, these elements cannot be reloaded or disabled. Reloading babel or config refreshes the data, but not the code.
 - Extensions are placed in the extensions folder, from there, they will be added to the config and can be enabled.
 - Config and config history will be found in the config folder.
 - Translation data is stored in the babel folder.
 - Error and usage logs are stored in the logs folder.

## Extensions
| Extension | Description | Ver. Added |
| ------ | ----------- | ----- |
| [main](main.py)* | imports extensions, creates some global variables, establishes a log, and runs the main loop | N/A |
| [config](config.py)* | reads configuration data and ensures that the config file is valid | 1.0 |
| [babel](babel.py)* | provides translated and formatted strings that contributors can easily translate to more languages | 1.0 |
| [auth](extensions/__auth.py)* | provides security checks for other commands which need authorization | 1.0 |
| [error](extensions/error.py) | provides error handling for all other extensions so they don't have to | 1.0 |
| [log](extensions/log.py) | allows for logging to file, or to a text channel in a rich format | 1.0 |
| [help](extensions/help.py)** | `help, about` - lists featured commands and fetches translated usage instructions | 1.0 |
| [language](extensions/language.py) | `language` - allows bot users to change the language or request a translation | 1.0 |
| [admin](extensions/admin.py) | `die, janitor, clean, purge` - power tools for server administrators | 1.0 |
| [dice](extensions/dice.py) | `dice` - a simple dice rolling command with some advanced features | 1.0 |
| [emoji](extensions/emoji.py) | `emoji, thonk` - allows non-nitro users to use a selection of custom emojis | 1.0 |
| [eventmsg](extensions/eventmsg.py) | `eventmsg` - automated messages in response to user actions | 1.0 |
| [poll](extensions/poll.py) | `poll` - adds polls to discord with an interactive poll builder and countdown timers | 1.0 |
| [reactroles](extensions/reactroles.py) | `reactrole` - adds reaction roles to discord with an interactive setup | 1.0 |
| [prefix](extensions/prefix.py) | `prefix` - allows guilds to have a custom prefix to use when this bot | 1.0 |
| [system](extensions/system.py) | `module, die` - modify behaviour of the bot while it's running | 1.2 |
| [premium](extensions/premium.py) | `premium` - locks select features behind a paywall, using a premium role to check | 1.0 |
| ------ | ----------- | ----- |
| [example](extensions/example.py) | `ping` - example commands for getting started on writing your own extension | 1.0 |

 - \* = must be imported for minimal functionality
 - \*\* = must be imported, or replaced with a compatible replacement
