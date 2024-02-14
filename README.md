![Merely logo](profile.png)
# Merelybot
![Python build status](https://github.com/yiays/merely/workflows/merelybot/badge.svg?branch=master)
**Merelybot is an extended feature-set for python Discord bots. Adding features like live reloading of code, a feature rich help command, translation support, error handling, and paywalled commands.**

## Featured implementations
You can test these implementations on my [official Discord server](https://discord.gg/wfKx24kDUR).
 - [Merely](https://discordapp.com/oauth2/authorize?client_id=309270899909984267&scope=bot&permissions=0) is an example implementation of the framework. Merely uses the default config included with this code so you can run it yourself.
 - [ConfessionBot](https://github.com/yiays/ConfessionBot-2.0) is an anonymous messaging system for Discord. ConfessionBot uses the help command, translation support, and module reloading features to speed up development and shares improvements to the framework back here.

## News
Seven languages are now supported! English, German, French, Polish, Brazilian Portugese, Tagalog, and Chinese are all available to choose with `/language set` today, but most are incomplete. *MerelyBot now also follows your user and server language preferences by default.*
> [See live translation stats and contribute >](https://translate.yiays.com)

MerelyBot v1.2.0 has launched! This update marks the completed migration to slash commands, which comes with countless performance and usability improvements. Some highlights are the newly-polished `/poll` and ReactRoles now catch up after any interruptions.
> [See the roadmap for future updates >](https://github.com/orgs/MerelyServices/projects/1)

## Usage
 - Clone the project to a folder
 - Install python <=3.10
 - Install required python packages with `python3 -m pip install -r requirements.txt`
 - Create a discord bot in the [Discord Developer Portal](https://discordapp.com/developers/applications/), you will need the token to continue
 - Give MerelyBot the token by setting it in the [main] section of the config
 - Run MerelyBot with `python3 merelybot.py`
 - Add your instance of merely to your server
 - *optional*: create a log channel on your server and copy the id to merely_data/config.ini > logchannel. - you can also do the same with a channel for feedback and a channel for moderators.

The first run generates a `config.ini` file, you can modify it from there to enable features.

## Contributing
The best way to contribute is to create your own discord bot using this framework, and send any improvements to the framework my way in the form of a pull request!

### Translation
I have built a website which makes it easier to translate my projects, including Merely-Framework. [Babel Translator](https://translate.yiays.com).

### Code contribution
Merely-Framework is written in Python with the help of the disnake API wrapper (like discord.py). Refer to the [Project roadmap](https://github.com/orgs/MerelyServices/projects/1) for future features we'd like to implement. All contributions are welcome and support can be given in the [Discord server](https://discord.gg/wfKx24kDUR).

### Design
Merely is a highly customizable and extensible framework for discord bots. through the config file, people can enable and disable extensions, change the bot name, and configure extensions. Developers can even write their own extensions to further extend the Merely Framework.

### Code structure
Extensions should operate entirely independant of each other and should rarely need to communicate with each other. Extensions must inherit from the [disnake.ext.commands.Cog](https://docs.disnake.dev/en/latest/ext/commands/api.html#cog) class and bind themselves on import. Effort should be made to avoid clashes with existing commands. [extensions/example.py](extensions/example.py) should demonstrate all of this.

For major extensions that create an entirely different category of bot (like my own ConfessionBot), an overlay system will soon be implemented so it's easier to update the framework without affecting overrides.

#### Strings
As the Babel language framework is being used, there's no need to provide strings for your code. Myself and the volunteer translators can add strings later. In place of strings, simply invent a meaningful key, for example;

```py
self.bot.babel('example', 'echo', content=userinput)
# Appears like the following until a string is written:
"<ECHO: content={content}>"
# An example of a written string:
"You said: \"{content}\"."
```

If you wish to provide strings, add them to `babel/en.ini`.

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
