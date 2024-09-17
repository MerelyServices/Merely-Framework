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
### Modal components can't be declared in `__init__`
Instead, create component class variables directly

---
### `Modal.callback` is now `Modal.on_submit`

---
### Context menu commands cannot be created inside a Cog
Refer to this https://github.com/Rapptz/discord.py/issues/7823#issuecomment-1086830458

---
### `inter.data` is now a low level component in Discord.py and offers no hand-holding
Data must be retreived manually, or just talk to the existing components as their state changes
- `inter.data.values` is now `inter.data['values']`
- `inter.data.custom_id` is now `inter.data['custom_id']`

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
### `TextInput.value` is now `TextInput.default`

---
### `allowed_contexts` and `allowed_installs` cannot be mixed with `_guild_ids`

