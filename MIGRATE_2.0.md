# Migrate to MerelyBot Framework 2.0

The Python Discord library space continues to be unstable, so in order to keep up with new features added to Discord, we are once again migrating libraries. This time, from Disnake back to Discord.py.

This migration has mostly been done for you by migrating MerelyBot-Framework, but there are a handful of changes you should be aware of;

---
### Most `@command.*` decorators are now `@app_command.*` decorators
If information relating to a decorator is sent to Discord (command name, description, parameters, allowed contexts, etc), import app_command and rename the decorator.
- Be sure to import `app_commands` using `from discord import app_commands`

---
### `Command.guild_ids` is now `@app_commands.guilds()` or `Command._guild_ids`

---
### `@commands.sub_command` no longer exists
The way command groups work is very different. In Discord.py, you need to explicitly identify command groups by creating an `app_commands.Group` instance.
- Sub commands use the `@groupname.command` decorator instead.
- You might also need to manually add the group as a command using `add_command`.

---
### `Bot` will attempt to add `**kwargs` to commands
This means no calling commands internally with additional arguments
- For Merely Framework, this means calling `bot.cogs['Help'].help(cmd, ephemeral=True)` is no longer possible.
  - Our solution; `send_message(bot.cogs['Help].resolve_help(cmd), ephemeral=True)`

---
### `Command.autocomplete` must return a list of `app_commands.Choice`s
A plus-side of this pattern is all choices have a name and value.

---
### Command parameters can no longer be described in the command docstring
Instead, use `@app_commands.describe(**kwargs)`.

---
### `Client.slash_commands` is now `Client.tree.walk_commands()`

---
### Modal components can't be declared in `__init__`
Instead, create component class variables directly

---
### `Modal.callback` is now `Modal.on_submit`

---
### `View`s are required, raw components are not available
This means you must always have a full lifecycle for your views planned; if the View is meant to survive restarts, you need to use `MerelyBot.config` and `@commands.Cog.listener('on_ready')` to rehydrate it.
- Be considerate when using the on_ready event! Consider adding a `asyncio.sleep()` so not all on_ready events fire at the same time.

---
### `Button.callback` has a different signature
`Interaction` is before `Button` now

---
### Context menu commands cannot be created inside a Cog
Refer to this https://github.com/Rapptz/discord.py/issues/7823#issuecomment-1086830458

---
### `inter.data` is now a low level component in Discord.py and offers no hand-holding
Data must be retreived manually, or just talk to the existing components as their state changes
- `inter.data.values` is now `inter.data.get('values')`
- `inter.data.custom_id` is now `inter.data.get('custom_id')`

---
### Calling commands internally is a little different
Instead of `self.command(inter)`, you need to call `self.command.callback(self, inter)`

---
### Most interaction events are not available
Instead we rely upon the low-level `on_interaction` event, or use Object callbacks
- `on_button_click`, `on_select` no longer exist

---
### Other events have been renamed
- `on__slash_command_completion` becomes `on_app_command_completion`

---
### Some functions now have positional only arguments
- `Embed.set_image()` is now positional only
- `Message.edit()` is now positional only

---
### Discord.py is more picky about typing being correct in default parameter values
- Danny has given us a list of types and will not allow us to stray away

---
### Everything is async now
- `autocomplete` functions must be async
- `load_extension` must be async, alongside Cog setup functions and bot.add_cog

---
### `getch` methods no longer exist
These handy methods automatically use fetch or get depending on cache, you will need to do this manually now

---
### `TextInput.value` is now `TextInput.default`

---
### `allowed_contexts` and `allowed_installs` cannot be mixed with `_guild_ids`

---
### `Channel.purge(before, after)` no longer accept `int`s.
Provide a `discord.Object(id)` instead