"""
  ReactRoles - Adds and takes roles based on a reaction to a message
  In the process of being replaced by EventMsg
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Iterable
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import emoji as ej
from emoji import unicode_codes

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


class ReactRoles(commands.Cog):
  """ Allows admins to set up messages where reacting grants users roles """
  SCOPE = 'reactroles'
  drafts:dict[int, ReactRoleEditorView]

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: str | bool) -> str:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, fallback=None, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)

    self.watching:dict[int, discord.Message] = {}
    self.drafts = {}

  # Utility functions

  async def get_roles(self, guild:discord.Guild, configid:str) -> set[discord.Role] | None:
    if configid in self.config:
      roleids = [
        int(r) for r in self.config[configid].split(' ')
      ]
      roles:set[discord.Role] = set()
      for roleid in roleids:
        try:
          role = guild.get_role(roleid)
          if role:
            roles.add(role)
        except Exception as e:
          print("failed to get role for reactrole: "+str(e))
      return roles
    return None

  async def change_roles(
    self,
    member:discord.Member,
    give:set[discord.Role] = set(),
    take:set[discord.Role] = set(),
    reason='reactroles',
    dm=True
  ) -> int:
    if len(give) + len(take) == 0:
      return 0
    # If give and take contradict, give wins
    for role in give:
      if role in take:
        take.remove(role)
    # Don't add roles that the member already has
    for role in member.roles:
      if role in give:
        give.remove(role)
    # Don't take roles that the member already doesn't have
    take = take & set(member.roles)
    # Action on the remaining roles and notify the user in DMs
    try:
      if len(give):
        await member.add_roles(*give, reason=reason)
      if len(take):
        await member.remove_roles(*take, reason=reason)
    except discord.Forbidden:
      if dm:
        try:
          await member.send(self.babel(member, 'role_change_failed_perms'))
        except discord.Forbidden:
          pass
    except discord.HTTPException:
      pass
    else:
      try:
        if len(give)+len(take) > 0 and dm:
          #BABEL: role_change
          await member.send(self.babel(
            member,
            'role_change',
            taken=self.bot.babel.string_list(member, [role.name for role in take]) if take else False,
            given=self.bot.babel.string_list(member, [role.name for role in give]) if give else False,
            server=member.guild.name
          ))
      except discord.HTTPException:
        pass
    return len(give)+len(take)

  async def catchup(self, messages:Iterable[discord.Message]):
    """ Give and take roles as needed to catch up to reality """
    changecount = 0
    guilds = set(m.guild for m in messages)
    for guild in guilds:
      assert guild is not None
      members = [m async for m in guild.fetch_members()]
      pendingchanges: dict[discord.Member, dict[bool, set[discord.Role]]]
      pendingchanges = {m: {True: set(), False: set()} for m in members}

      for msg in messages:
        if msg.guild == guild:
          for (message_id, emojiid, roleconfid) in (c.split('_')[1:3] + [c] for c in self.config):
            if int(message_id) == msg.id:
              emoji = await guild.fetch_emoji(int(emojiid)) if emojiid.isdecimal() else emojiid
              if emoji not in (r.emoji for r in msg.reactions):
                await msg.add_reaction(emoji)
              if roles := await self.get_roles(guild, roleconfid):
                reacts = [r for r in msg.reactions if r.emoji == emoji]
                if not reacts:
                  continue
                react = reacts[0]
                reactors = [u async for u in react.users()]
                for member in members:
                  if member == self.bot.user or member.bot:
                    continue
                  if (
                    member in reactors and
                    not all(memberrole in roles for memberrole in member.roles)
                  ):
                    pendingchanges[member][True].update(roles)
                  elif (
                    member not in reactors and
                    any(memberrole in roles for memberrole in member.roles)
                  ):
                    pendingchanges[member][False].update(roles)
                if self.bot.user not in reactors:
                  # Add back bot reactions if they were deleted
                  await msg.add_reaction(react.emoji)

          for member in members:
            give = pendingchanges[member][True].difference(pendingchanges[member][False])
            take = pendingchanges[member][False].difference(pendingchanges[member][False])
            changecount += await self.change_roles(member, give, take, 'reactroles catchup')

    return changecount

  # Events

  @commands.Cog.listener("on_ready")
  async def fetch_tracking_messages(self):
    """ Request the message once so we'll be notified if reactions change """
    print("reactroles catchup started")
    deleted = 0
    for key in self.config.keys():
      chid,msgid = (int(id) for id in key.split('_', 3)[:2])
      msg: discord.Message
      try:
        ch = await self.bot.fetch_channel(chid)
        assert isinstance(ch, discord.abc.Messageable)
        msg = await ch.fetch_message(msgid)
        self.watching[msg.id] = msg
      except discord.NotFound:
        self.config.pop(key)
        deleted += 1
      except Exception as e:
        print(f"failed to get reactionrole message {msgid} from channel {chid}. {e}")
        continue
    changes = await self.catchup(self.watching.values())
    print("reactroles catchup ended. Delta: ", changes, "Deletes: ", deleted)
    if deleted:
      self.bot.config.save()

  @commands.Cog.listener("on_message_delete")
  async def revoke_tracking_message(self, message:discord.Message):
    """ Remove message from config so it won't attempt to load it again """
    for k in self.config.keys():
      if k.split('_')[1] == str(message.id):
        if not self.bot.quiet:
          print("Removed", k, "from reactroles config.")
        self.config.pop(k)
        self.bot.config.save()
        break
    if message.id in self.watching:
      self.watching.pop(message.id)
    if message.channel.id in self.drafts and message.id == self.drafts[message.channel.id].msg.id:
      self.drafts.pop(message.channel.id)

  @commands.Cog.listener("on_raw_reaction_add")
  async def reactrole_reaction_add(self, data:discord.RawReactionActionEvent):
    """ Grant the user their role """
    assert self.bot.user is not None
    if data.user_id == self.bot.user.id or data.guild_id is None:
      return
    if isinstance(data.member, discord.Member):
      emojiid = data.emoji if data.emoji.is_unicode_emoji() else data.emoji.id
      if data.channel_id in self.drafts and data.message_id == self.drafts[data.channel_id].msg.id:
        # Don't allow reactions until the draft is published
        await self.drafts[data.channel_id].msg.remove_reaction(data.emoji, data.member)
        return

      roleconfid = f"{data.channel_id}_{data.message_id}_{emojiid}_roles"
      if roles := await self.get_roles(data.member.guild, roleconfid):
        await self.change_roles(data.member, give=roles)

  @commands.Cog.listener("on_raw_reaction_remove")
  async def reactrole_reaction_remove(self, data:discord.RawReactionActionEvent):
    """ Take back roles """
    assert self.bot.user is not None
    if data.guild_id is None:
      return
    if data.user_id == self.bot.user.id:
      # Bot reaction was manually removed
      if data.channel_id in self.drafts and data.message_id == self.drafts[data.channel_id].msg.id:
        # Remove reactrole if in draft mode
        await self.drafts[data.channel_id].remove_reactroles(data.emoji)
      elif data.message_id in self.watching:
        # Add deleted reaction back otherwise
        await self.watching[data.message_id].add_reaction(data.emoji)
    else:
      # Member potentially removed their reaction to a reactrole
      guild = self.bot.get_guild(data.guild_id)
      assert guild is not None
      member = await guild.fetch_member(data.user_id)
      emojiid = data.emoji if data.emoji.is_unicode_emoji() else data.emoji.id
      roleconfid = f"{data.channel_id}_{data.message_id}_{emojiid}_roles"
      if roles := await self.get_roles(member.guild, roleconfid):
        await self.change_roles(member, take=roles)

  @commands.Cog.listener("on_raw_reaction_clear")
  @commands.Cog.listener("on_raw_reaction_clear_emoji")
  async def reactrole_reaction_clear(
    self, data:(discord.RawReactionClearEvent | discord.RawReactionClearEmojiEvent)
  ):
    if data.channel_id in self.drafts and data.message_id == self.drafts[data.channel_id].msg.id:
      # Remove reactroles if the original reaction is removed while in draft mode
      #NOTE: This will cause issues if another way to remove reactroles is added
      if isinstance(data, discord.RawReactionClearEmojiEvent):
        await self.drafts[data.channel_id].remove_reactroles(data.emoji)
      else:
        await self.drafts[data.channel_id].reset_reactroles()
    elif data.message_id in self.watching:
      # State of reactions has drastically changed, run catchup on this message
      message = await self.watching[data.message_id].channel.fetch_message(data.message_id)
      await self.catchup((message,))

  # Views

  class ReactRoleEditorView(discord.ui.View):
    """ Draft ReactRole message state and editor """
    #TODO: make it possible to reopen this editor later
    msg:discord.Message

    def __init__(
        self,
        parent:ReactRoles,
        inter: discord.Interaction,
        prompt:str
      ):
      super().__init__(timeout=300)

      self.parent = parent
      self.inter = inter
      self.prompt = prompt
      self.react_roles: dict[int | str, list[discord.Role]] = {}

      self.add_reaction_button.label = parent.babel(inter, 'add_reaction')
      self.save_button.label = parent.babel(inter, 'save_button')

    async def add_reactroles(
      self, emoji:discord.Emoji | discord.PartialEmoji | str, roles:list[discord.Role]
    ):
      """ Add an emoji and roles list to this message """
      emojiid: str | int
      if isinstance(emoji, discord.Emoji):
        emojiid = emoji.id
      elif isinstance(emoji, str):
        emojiid = emoji
      elif emoji.is_unicode_emoji():
        emojiid = str(emoji)
      self.timeout = 300
      self.react_roles[emojiid] = roles
      await self.msg.add_reaction(emoji)
      if self.save_button.disabled:
        self.save_button.disabled = False
        await self.msg.edit(view=self)

    async def remove_reactroles(self, emoji:discord.Emoji | discord.PartialEmoji | str):
      """ Remove an emoji and roles list from this message """
      emojiid: str | int
      if isinstance(emoji, discord.Emoji):
        emojiid = emoji.id
      elif isinstance(emoji, str):
        emojiid = emoji
      elif emoji.is_unicode_emoji():
        emojiid = str(emoji)
      else:
        assert self.msg.guild is not None and emoji.id is not None
        fullemoji = self.msg.guild.get_emoji(emoji.id)
        if fullemoji:
          emoji = fullemoji
      self.timeout = 300
      self.react_roles.pop(emojiid)
      await self.msg.reply(self.parent.babel(self.msg, 'emoji_removed', emoji=str(emoji)))
      if len(self.react_roles) < 1:
        self.save_button.disabled = True
        await self.msg.edit(view=self)

    async def reset_reactroles(self):
      """ Clear all emoji and roles lists from this message """
      self.timeout = 300
      elist = self.parent.bot.babel.string_list(self.msg, [str(e) for e in self.react_roles])
      self.react_roles = {}
      await self.msg.reply(self.parent.babel(self.msg, 'emoji_removed', emoji=elist))
      self.save_button.disabled = True
      await self.msg.edit(view=self)

    @discord.ui.button(style=discord.ButtonStyle.green, emoji='❔', custom_id='add_reactrole_emoji')
    async def add_reaction_button(self, inter:discord.Interaction, _:discord.Button):
      """ Sends the command needed to add a reaction (and associated roles) """
      self.parent.bot.auth.admins(inter)

      await inter.response.send_message(
        self.parent.babel(inter, 'howto_add_reaction', cmd='reactrole_add'),
        ephemeral=True
      )

    @discord.ui.button(
      style=discord.ButtonStyle.primary, emoji='💾', disabled=True, custom_id='reactrole_submit'
    )
    async def save_button(self, inter:discord.Interaction, _:discord.Button):
      """ Saves the reactrole message to storage so it will start to take effect """
      self.parent.bot.auth.admins(inter)
      assert inter.channel is not None

      await self.msg.edit(view=None)

      for emojiid, roles in self.react_roles.items():
        roleconfid = f"{inter.channel.id}_{self.msg.id}_{emojiid}_roles"
        self.parent.config[roleconfid] = ' '.join([str(r.id) for r in roles])
        assert inter.guild is not None
        emoji = inter.guild.get_emoji(emojiid) if isinstance(emojiid, int) else emojiid

        # add reactions again in the background (just in case they've been cleared)
        if emoji:
          asyncio.ensure_future(self.msg.add_reaction(emoji))

      self.parent.bot.config.save()
      self.parent.watching[self.msg.id] = self.msg
      self.parent.drafts.pop(inter.channel.id)

    async def on_timeout(self):
      assert self.msg.guild is not None
      self.save_button.disabled = True
      self.add_reaction_button.disabled = True
      try:
        await self.msg.edit(
          content=self.parent.bot.babel(self.msg.guild, 'error', 'timeoutview'),
          view=self
        )
      except discord.HTTPException:
        pass

  # Utilities

  def find_locale(self, inter:discord.Interaction):
    """ Determine the locale of the user, based on config and server settings """
    langs = self.bot.babel.resolve_lang(inter.user.id, inter.guild_id, inter)
    i = 0
    lang = langs[i]
    if prefix := self.bot.config['language']['prefix']:
      # Overlay support: continue down the chain of inheritance until a base language is found
      while lang.startswith(prefix):
        i += 1
        lang = langs[i]
    return lang

  # Commands

  @app_commands.command(
    name=app_commands.locale_str('reactrole_add', scope=SCOPE),
    description=app_commands.locale_str('reactrole_add_desc', scope=SCOPE)
  )
  @app_commands.describe(
    emoji=app_commands.locale_str('reactrole_add_emoji_desc', scope=SCOPE),
    role1=app_commands.locale_str('reactrole_add_role_desc', scope=SCOPE),
    role2=app_commands.locale_str('reactrole_add_role_desc', scope=SCOPE),
    role3=app_commands.locale_str('reactrole_add_role_desc', scope=SCOPE),
  )
  @app_commands.guild_only()
  @app_commands.default_permissions(administrator=True)
  async def reactrole_edit_add(
    self,
    inter:discord.Interaction,
    emoji:str,
    role1:discord.Role,
    role2:Optional[discord.Role] = None,
    role3:Optional[discord.Role] = None
  ):
    """
      Add a reaction and the corresponding roles to a prompt in edit mode.
    """
    assert inter.guild is not None

    emoji = emoji.strip().replace(':', '')
    lang = self.find_locale(inter)[2:]

    if inter.channel_id not in self.drafts:
      await inter.response.send_message(self.babel(inter, 'no_draft'), ephemeral=True)
      return
    foundemoji:discord.Emoji | str
    if ej.is_emoji(emoji):
      # Emoji keyboard emoji
      foundemoji = emoji
    elif emoji.isdigit():
      # Discord server emoji (by id)
      try:
        foundemoji = await inter.guild.fetch_emoji(int(emoji))
      except discord.NotFound:
        await inter.response.send_message(self.babel(inter, 'no_emoji'), ephemeral=True)
        return
    elif matches := [e for e in inter.guild.emojis if e.name == emoji]:
      # Discord server emoji (by name)
      foundemoji = matches[0]
    elif match := unicode_codes.get_emoji_by_name(f':{emoji}:', lang):
      # UTF Emoji (by name)
      foundemoji = match
    else:
      await inter.response.send_message(self.babel(inter, 'no_emoji'), ephemeral=True)
      return

    _roles = set((role1, role2, role3))
    roles: set[discord.Role] = {role for role in _roles if role is not None}
    unassignable = []
    for role in roles:
      if not role.is_assignable():
        unassignable.append('"'+role.name+'"')
    if unassignable:
      assert isinstance(inter.channel, discord.abc.Messageable)
      await inter.channel.send(self.babel(
        inter,
        'warn_unassignable',
        myrole=inter.guild.me.top_role.name,
        roles=self.bot.babel.string_list(inter, unassignable)
      ))

    await self.drafts[inter.channel_id].add_reactroles(foundemoji, list(roles))
    await inter.response.send_message(self.babel(inter, 'emoji_added'), ephemeral=True)

  @reactrole_edit_add.autocomplete('emoji')
  async def ac_emoji(self, inter:discord.Interaction, search:str):
    """ Autocomplete for emoji search """
    assert inter.guild is not None

    search = search.strip()
    lang = self.find_locale(inter)[2:]
    if lang not in ej.EMOJI_DATA['🤣']:
      # Fallback to en if the language is not supported
      lang = 'en'

    results = [
      app_commands.Choice(name=f':{e.name}:', value=str(e.id))
      for e in inter.guild.emojis
      if search.replace(':','').lower() in e.name.lower()
      or f'{e.name}:{e.id}' in search
    ] + [
      app_commands.Choice(name=f'{e} {ej.EMOJI_DATA[e][lang]} (built in)', value=e)
      for e in ej.EMOJI_DATA
      if search.lower() in ej.EMOJI_DATA[e][lang].lower()
      or search == e
    ]
    return results[:25]

  @app_commands.command(
    name=app_commands.locale_str('reactrole', scope=SCOPE),
    description=app_commands.locale_str('reactrole_desc', scope=SCOPE)
  )
  @app_commands.describe(topic=app_commands.locale_str('reactrole_topic_desc', scope=SCOPE))
  @app_commands.guild_only()
  @app_commands.default_permissions(administrator=True)
  @commands.bot_has_permissions(read_messages=True, manage_messages=True, add_reactions=True)
  async def reactrole(self, inter:discord.Interaction, topic:str):
    """
      Grant members roles whenever they react to a message
    """
    assert inter.channel is not None
    if inter.channel.id in self.drafts:
      await inter.response.send_message(self.babel(inter, 'draft_in_progress'))
      return
    #TODO: save drafts to storage
    self.drafts[inter.channel.id] = self.ReactRoleEditorView(self, inter, topic)
    await inter.response.send_message(topic, view=self.drafts[inter.channel.id])
    self.drafts[inter.channel.id].msg = await inter.original_response()
    await inter.followup.send(
      self.babel(inter, 'howto_add_reaction', cmd='reactrole_add'),
      ephemeral=True
    )


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(ReactRoles(bot))
