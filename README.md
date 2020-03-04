# merelybot
merely is a bot that exists mostly to serve my own needs on my [discord server](https://discord.gg/f6TnEJM), however it also has some unique and complex commands that people on other servers seem to enjoy.

I categorise my commands based on their purpose. For interactive tutorials on how to use these commands, please refer to the [web UI](https://merely.yiays.com).

merely has a meme module, which acts as a meme source for [MemeDB](https://meme.yiays.com/).

# usage
 - clone the project to a folder
 - install required python packages with `pip3 install -r requirements.txt`
 - assign a discord token with
   - `export MerelyBeta="TOKEN"` on linux
   - `setx MerelyBeta "TOKEN"` on windows
 - run it with `python3 merelybot.py`

After the first run, you can enable commands by editing the file at merely_data/config.ini in order to enable modules. simply switch the value of each module you want from `False` to `True`, note that the meme module has external dependencies and will not work in a local environment yet.

# contributing
feel free to fix any bugs or add new features to a fork, and send me a pull request, pretty standard github stuff.

keep in mind this lowwercase thing is a theme of merely, consider it appealing to the customs of discord.

# modules
| module | description | added |
| ------ | ----------- | ----- |
| [main](merelybot.py)* | imports all modules, creates some global variables, and runs the main loop | 0.0.1 |
| [globals](globals.py)* | contains global variables and configuration data | 0.0.1 |
| [help](help.py)<sup>1</sup> | help contains help strings for all commands, lists of commands, lists of hints and other documentation. | 0.0.1 |
| [admin](admin.py) | commands restricted to mods and server owners | >0.5.0 |
| [censor](censor.py) | the blacklist, whitelist and algorithms used to determine if blacklisted words are in a string, also sass | >0.5.0 |
| [emformat](emformat.py) | useful functions for formatting strings into discord embeds |
| [fun](fun.py) | fun commands available to everyone, like `m/echo`, `m/vote` and `m/dice` | >0.5.0 |
| [meme](meme.py) | connects to [MemeDB](https://meme.yiays.com/) and provides commands and react buttons to interact with it. *legacy: stores and shares memes in a local database* | >0.5.0 |
| [search](search.py) | google, google images and help search libraries/commands | >0.5.0 |
| [stats](stats.py)<sup>1</sup> | statistics collection and storage, `m/stats` and [the stats page](https://merely.yiays.com/stats.html) (currently broken) | >0.5.0 |
| [webserver](webserver.py)<sup>1</sup> | serves [merely.yiays.com](https://merely.yiays.com/) | >0.5.0 |
| [obsolete](obsolete.py) | stores stubs for old obsolete commands and promotes merely music when someone attempts to use musicbot commands | >0.5.0 |
| [utils](utils.py) | provides useful general functions for programming merely | 0.7.3 |
| [tools](tools.py) | provides tools for all users (unlike admin, which is for mods and server owners) like `m/shorten` | 0.7.4 |

 - \* = must be imported for minimal functionality
 - <sup>n</sup> = these modules are codependant - they must be enabled together