![Merely logo](profile.png)
# Merelybot
![Python build status](https://github.com/yiays/merely/workflows/merelybot/badge.svg?branch=master)
**Merelybot is an extended feature-set framework for Discord.py bots. Adding features like configuration-defined bots, hot-reloading of code, a feature rich help command, translation support, authorization, security, error handling, and paywalled commands.**

## Featured implementations
You can test these implementations on my [official Discord server](https://discord.gg/wfKx24kDUR).
 - [Merely](https://discordapp.com/oauth2/authorize?client_id=309270899909984267&scope=bot&permissions=0) is an example implementation of the framework. Merely uses the default config included with this code so you can run it yourself.
 - [ConfessionBot](https://github.com/yiays/ConfessionBot-2.0) is an anonymous messaging system for Discord. ConfessionBot uses the help command, translation support, and module reloading features to speed up development and shares improvements to the framework back here.

## News
**MerelyBot v2.0 has launched!** This is a major release because we are changing the underlying library back to Discord.py in order to support user installation. This means you can now add Merely to your account and use the new command (`/download`) anywhere!
> [Migration advice for developers >](MIGRATE_2.0.md)

## Usage
 - Clone the project to a folder
 - Install python >= 3.10
 - Install required python packages with `python3 -m pip install -r requirements.txt`
 - Create a discord bot in the [Discord Developer Portal](https://discordapp.com/developers/applications/), you will need the token to continue
 - Give MerelyBot the token by setting it in the [main] section of the config
 - Run MerelyBot with `python3 merelybot.py`
 - Add your instance of merely to your server
 - *Optional*: change the behaviour and features of your bot in the `config/config.ini` file.
   - Restart the bot to apply changes.

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

#### Writing a different bot using the framework
If you would like to make a bot that changes functionality of existing commands or strings, you may want to use an overlay. Create a folder named 'overlay' in this directory, refer to the [source code for ConfessionBot](https://github.com/yiays/ConfessionBot/tree/beta) to see an example of how an overlay is structured. *Note that babel is given a language file prefix so Merely Language files can still be inherited from.*

This overlay system allows for improvements to the framework to be easily shared upstream and downstream.

#### Strings
As the Babel language framework is being used, there's no need to provide strings for your code. Myself and the volunteer translators can add strings later. In place of strings, simply invent a meaningful key, for example;

```py
self.bot.babel('example', 'echo', content=userinput)
# Appears like the following until a string is written:
"<ECHO: content={content}>"
# Appears like this after the string is written:
"You said: \"content\"."
```

In `babel/en.ini`;
```ini
[example]
echo = You said: "{content}"
```

### File structure
 - Core plugins are stored in the top directory, these elements cannot be disabled. Reloading babel or config refreshes the data, but not the code.
 - Extensions are placed in the extensions folder, from there, they will appear in the config and can be enabled.
 - Config and config history will be found in the config folder.
 - Translation data is stored in the babel folder.
 - Error and usage logs are stored in the logs folder.
 - Translations, config, and extensions can be overidden in an "overlay" folder.
 - Some extensions may create a "tmp" folder. This contains temporary files which are not needed after restarts.

## Extensions
| Extension | Description | Ver. Added |
| ------ | ----------- | ----- |
| [main](main.py)🔒 | Imports extensions, creates some global variables, establishes a log, and runs the main loop | N/A |
| [config](config.py)🔒 | Reads configuration data and ensures that the config file is valid | 1.0 |
| [babel](babel.py)🔒 | Provides translated and formatted strings that contributors can easily translate to more languages | 1.0 |
| [auth](auth.py)🔒 | Provides security checks for other commands which need authorization | 1.0 |
| [utilities](utilities.py)🔒 | Provides useful functions and other shared code between extensions | 1.2.2 |
| [error](extensions/error.py) | Provides error handling for all other extensions and informs the user | 1.0 |
| [log](extensions/log.py) | Logging to file, or to a text channel in a rich format | 1.0 |
| [help](extensions/help.py) | `help, about` - Lists featured commands and fetches translated usage instructions | 1.0 |
| [language](extensions/language.py) | `language` - Allows bot users to change the language | 1.0 |
| [admin](extensions/admin.py) | `janitor, clean, purge` - Power tools for server administrators | 1.0 |
| [dice](extensions/dice.py) | `dice` - A simple dice rolling command with some advanced features | 1.0 |
| [emoji](extensions/emoji.py) | `emoji, thonk` - Allows non-nitro users to use a selection of custom emojis | 1.0 |
| [eventmsg](extensions/eventmsg.py) | `eventmsg, welcome, farewell` - Automated messages in response to user actions *(replaces greeter)* | 1.0 |
| [poll](extensions/poll.py) | `poll` - Adds polls to discord with an interactive poll builder and countdown timers | 1.0 |
| [reactroles](extensions/reactroles.py) | `reactrole` - Adds reaction role automations to discord with an interactive setup | 1.0 |
| [system](extensions/system.py) | `module, migrate, die` - Advanced bot controls, deploy patches without restarting | 1.2 |
| [premium](extensions/premium.py) | `premium` - Locks select features behind a paywall, premium roles can bypass | 1.0 |
| [controlpanel](extensions/controlpanel.py) | `controlpanel` - Toggle user and guild settings for all modules in one place | 1.2 |
| [announce](extensions/announce.py) | `announce` - Send an announcement to server owners | 1.2.3 |
| [download](extensions/download.py) | `download` - Downloads videos from any public url and reuploads them to chat | 1.4.0 |
| ------ | ----------- | ----- |
| [example](extensions/example.py) | `echo` - Example commands for getting started on writing your own extension | 1.0 |
| [error_test](extensions/error_test.py) | `throw_error` - Creates errors intentionally to test error handling | 1.2 |

🔒 = This is a core component and cannot be disabled
