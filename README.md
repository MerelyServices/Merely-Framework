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

## executing
to run the bot in your own environment, install the requirements in requirements.txt, and create an environment variable with the name Merely and the value being a Discord Bot Token, and disable the meme module (a method to do this is being implemented).
