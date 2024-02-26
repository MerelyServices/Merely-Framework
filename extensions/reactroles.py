"""
  ReactRoles - Adds and takes roles based on a reaction to a message
  In the process of being replaced by EventMsg
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Iterable
import asyncio
import disnake
from disnake.ext import commands
import emoji as ej
import re

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable


class ReactRoles(commands.Cog):
  """ Allows admins to set up messages where reacting grants users roles """
  SCOPE = 'reactroles'
  drafts:dict[int, ReactRoleEditorView]

  @property
  def config(self) -> dict[str, str]:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)
    self.watching:dict[int, disnake.Message] = {}
    self.drafts = {}

  # Utility functions

  async def get_roles(self, guild:disnake.Guild, configid:str) -> set[disnake.Role] | None:
    if configid in self.config:
      roleids = [
        int(r) for r in self.config[configid].split(' ')
      ]
      roles:set[disnake.Role] = set()
      for roleid in roleids:
        try:
          roles.add(guild.get_role(roleid))
        except Exception as e:
          print("failed to get role for reactrole: "+str(e))
      return roles
    return None

  async def change_roles(
    self,
    member:disnake.Member,
    give:set[disnake.Role] = set(),
    take:set[disnake.Role] = set(),
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
    except disnake.Forbidden:
      if dm:
        await member.send(self.babel(member, 'role_change_failed_perms'))
    except disnake.HTTPException:
      pass
    else:
      try:
        if len(give)+len(take) > 0 and dm:
          await member.send(self.babel(
            member,
            'role_change',
            taken=self.bot.babel.string_list(member, [role.name for role in take]) if take else False,
            given=self.bot.babel.string_list(member, [role.name for role in give]) if give else False,
            server=member.guild.name
          ))
      except disnake.HTTPException:
        pass
    return len(give)+len(take)

  async def catchup(self, messages:Iterable[disnake.Message]):
    """ Give and take roles as needed to catch up to reality """
    changecount = 0
    guilds = set(m.guild for m in messages)
    for guild in guilds:
      members = await guild.fetch_members().flatten()
      pendingchanges: dict[disnake.Member, dict[bool, set[disnake.Role]]]
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
                reactors = await react.users().flatten()
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
      chid,msgid = key.split('_')[:2]
      msg: disnake.Message
      try:
        ch = await self.bot.fetch_channel(chid)
        msg = await ch.fetch_message(msgid)
      except disnake.NotFound:
        self.bot.config.remove_option(self.SCOPE, key)
        deleted += 1
      except Exception as e:
        print(f"failed to get reactionrole message {msgid} from channel {chid}. {e}")
        continue
      self.watching[msg.id] = msg
    changes = await self.catchup(self.watching.values())
    print("reactroles catchup ended. Delta: ", changes, "Deletes: ", deleted)
    if deleted:
      self.bot.config.save()

  @commands.Cog.listener("on_message_delete")
  async def revoke_tracking_message(self, message:disnake.Message):
    """ Remove message from config so it won't attempt to load it again """
    for k in self.config.keys():
      if k.split('_')[1] == str(message.id):
        self.bot.config.remove_option(self.SCOPE, k)
        self.bot.config.save()
        break
    if message.id in self.watching:
      self.watching.pop(message.id)
    if message.channel.id in self.drafts and message.id == self.drafts[message.channel.id].msg.id:
      self.drafts.pop(message.channel.id)

  @commands.Cog.listener("on_raw_reaction_add")
  async def reactrole_reaction_add(self, data:disnake.RawReactionActionEvent):
    """ Grant the user their role """
    if data.user_id == self.bot.user.id or data.guild_id is None:
      return
    if isinstance(data.member, disnake.Member):
      emojiid = data.emoji if data.emoji.is_unicode_emoji() else data.emoji.id
      if data.channel_id in self.drafts and data.message_id == self.drafts[data.channel_id].msg.id:
        # Don't allow reactions until the draft is published
        await self.drafts[data.channel_id].msg.remove_reaction(emojiid, data.member)
        return

      roleconfid = f"{data.channel_id}_{data.message_id}_{emojiid}_roles"
      if roles := await self.get_roles(data.member.guild, roleconfid):
        await self.change_roles(data.member, give=roles)

  @commands.Cog.listener("on_raw_reaction_remove")
  async def reactrole_reaction_remove(self, data:disnake.RawReactionActionEvent):
    """ Take back roles """
    if data.guild_id is None:
      return
    if data.user_id == self.bot.user.id:
      # Bot reaction was manually removed
      if data.channel_id in self.drafts and data.message_id == self.drafts[data.channel_id].msg.id:
        # Remove reactrole if in draft mode
        if data.emoji.is_unicode_emoji():
          emoji = str(data.emoji)
        else:
          emoji = await self.bot.get_guild(data.guild_id).fetch_emoji(data.emoji.id)
        await self.drafts[data.channel_id].remove_reactroles(emoji)
      elif data.message_id in self.watching:
        # Add deleted reaction back otherwise
        await self.watching[data.message_id].add_reaction(data.emoji)
    else:
      # Member potentially removed their reaction to a reactrole
      member = await self.bot.get_guild(data.guild_id).getch_member(data.user_id)
      emojiid = data.emoji if data.emoji.is_unicode_emoji() else data.emoji.id
      roleconfid = f"{data.channel_id}_{data.message_id}_{emojiid}_roles"
      if roles := await self.get_roles(member.guild, roleconfid):
        await self.change_roles(member, take=roles)

  @commands.Cog.listener("on_raw_reaction_clear")
  @commands.Cog.listener("on_raw_reaction_clear_emoji")
  async def reactrole_reaction_clear(
    self, data:(disnake.RawReactionClearEvent | disnake.RawReactionClearEmojiEvent)
  ):
    if data.channel_id in self.drafts and data.message_id == self.drafts[data.channel_id].msg.id:
      # Remove reactroles if the original reaction is removed while in draft mode
      #NOTE: This will cause issues if another way to remove reactroles is added
      if isinstance(data, disnake.RawReactionClearEmojiEvent):
        if data.emoji.is_unicode_emoji():
          emoji = str(data.emoji)
        else:
          emoji = self.bot.get_guild(data.guild_id).fetch_emoji(data.emoji.id)
        await self.drafts[data.channel_id].remove_reactroles(emoji)
      else:
        await self.drafts[data.channel_id].reset_reactroles()
    elif data.message_id in self.watching:
      # State of reactions has drastically changed, run catchup on this message
      message = await self.watching[data.message_id].channel.fetch_message(data.message_id)
      await self.catchup((message,))

  # Views

  class ReactRoleEditorView(disnake.ui.View):
    """ Draft ReactRole message state and editor """
    #TODO: make it possible to reopen this editor later
    msg:disnake.Message

    def __init__(
        self,
        parent:ReactRoles,
        inter: disnake.GuildCommandInteraction,
        prompt:str
      ):
      super().__init__(timeout=300)

      self.parent = parent
      self.inter = inter
      self.prompt = prompt
      self.react_roles: dict[disnake.Emoji | str, list[disnake.Role]] = {}

      self.add_reaction_button.label = parent.babel(inter, 'add_reaction')
      self.save_button.label = parent.babel(inter, 'save_button')

    async def add_reactroles(self, emoji:disnake.Emoji | str, roles:list[disnake.Role]):
      self.timeout = 300
      self.react_roles[emoji] = roles
      await self.msg.add_reaction(emoji)
      if self.save_button.disabled:
        self.save_button.disabled = False
        await self.msg.edit(view=self)

    async def remove_reactroles(self, emoji:disnake.Emoji | str):
      self.timeout = 300
      self.react_roles.pop(emoji)
      await self.msg.reply(self.parent.babel(self.msg.guild, 'emoji_removed', emoji=emoji))
      if len(self.react_roles) < 1:
        self.save_button.disabled = True
        await self.msg.edit(view=self)

    async def reset_reactroles(self):
      self.timeout = 300
      elist = self.parent.bot.babel.string_list(self.msg.guild, [str(e) for e in self.react_roles])
      self.react_roles = {}
      await self.msg.reply(self.parent.babel(self.msg.guild, 'emoji_removed', emoji=elist))
      self.save_button.disabled = True
      await self.msg.edit(view=self)

    @disnake.ui.button(style=disnake.ButtonStyle.green, emoji='❔')
    async def add_reaction_button(self, _:disnake.Button, inter:disnake.MessageInteraction):
      """ Sends the command needed to add a reaction (and associated roles) """
      self.parent.bot.auth.admins(inter)

      await inter.response.send_message(
        self.parent.babel(inter, 'howto_add_reaction', cmd='/reactrole_add'),
        ephemeral=True
      )

    @disnake.ui.button(style=disnake.ButtonStyle.primary, emoji='💾', disabled=True)
    async def save_button(self, _:disnake.Button, inter:disnake.MessageInteraction):
      """ Saves the reactrole message to storage so it will start to take effect """
      self.parent.bot.auth.admins(inter)

      await self.msg.edit(view=None)

      for emoji, roles in self.react_roles.items():
        emojiid = emoji if isinstance(emoji, str) else emoji.id
        roleconfid = f"{inter.channel.id}_{self.msg.id}_{emojiid}_roles"
        self.parent.config[roleconfid] = ' '.join([str(r.id) for r in roles])

        # add reactions again in the background (just in case they've been cleared)
        asyncio.ensure_future(self.msg.add_reaction(emoji))

      self.parent.bot.config.save()
      self.parent.watching[self.msg.id] = self.msg
      self.parent.drafts.pop(inter.channel_id)

    async def on_timeout(self):
      self.save_button.disabled = True
      self.add_reaction_button.disabled = True
      try:
        await self.msg.edit(self.parent.bot.babel(self.msg.guild, 'error', 'timeoutview'))
      except disnake.HTTPException:
        pass

  # Commands

  @commands.guild_only()
  @commands.slash_command(name='reactrole_add')
  @commands.default_member_permissions(administrator=True)
  async def reactrole_edit_add(
    self,
    inter:disnake.CommandInteraction,
    emoji:str,
    role1:disnake.Role,
    role2:Optional[disnake.Role] = None,
    role3:Optional[disnake.Role] = None
  ):
    """
    Add a reaction and the corresponding roles to a prompt in edit mode.

    Parameters
    ----------
    emoji: The emoij to be used
    role1: The first role to be given to users that react with this emoji
    role2: The second role to be given to users that react with this emoji
    role3: The third role to be given to users that react with this emoji
    """
    emoji = emoji.strip()
    lang = self.bot.babel.resolve_lang(inter.user.id, inter.guild_id, inter)[0]
    all_emoji = ej.unicode_codes.get_emoji_unicode_dict(lang)

    if inter.channel_id not in self.drafts:
      await inter.response.send_message(self.babel(inter, 'no_draft'), ephemeral=True)
      return
    foundemoji:disnake.Emoji | str
    if ej.is_emoji(emoji.split()[0]):
      # Emoji keyboard emoji
      foundemoji = emoji.split()[0]
    elif match := re.match(r'<a?:[\w\d\_]+:([\d]+)>', emoji):
      # Discord server emoji (by id)
      match:re.Match[str]
      try:
        foundemoji = await inter.guild.fetch_emoji(int(match.groups()[0]))
      except disnake.NotFound:
        await inter.response.send_message(self.babel(inter, 'no_emoji'), ephemeral=True)
        return
    elif match := [e for e in inter.guild.emojis if e.name == emoji.replace(':', '')]:
      # Discord server emoji (by name)
      foundemoji = match[0]
    elif match := [e for e in all_emoji if e == emoji or e == f':{emoji}:']:
      # UTF Emoji (by name)
      foundemoji = all_emoji[emoji]
    else:
      await inter.response.send_message(self.babel(inter, 'no_emoji'), ephemeral=True)
      return

    roles = set((role1, role2, role3))
    roles.remove(None)
    await self.drafts[inter.channel_id].add_reactroles(foundemoji, list(roles))
    await inter.response.send_message(self.babel(inter, 'emoji_added'), ephemeral=True)

  @reactrole_edit_add.autocomplete('emoji')
  def ac_emoji(self, inter:disnake.CommandInteraction, search:str):
    """ Autocomplete for emoji search """
    search = search.strip()
    lang = self.bot.babel.resolve_lang(inter.user.id, inter.guild_id, inter)[0]
    all_emoji = ej.unicode_codes.get_emoji_unicode_dict(lang)

    results = [
      f':{e.name}:' for e in inter.guild.emojis
      if search.replace(':','').lower() in e.name.lower()
      or f'{e.name}:{e.id}' in search
    ] + [
      f'{all_emoji[e]} {e} (built in)' for e in all_emoji
      if search.lower().replace(':','') in e.lower()
      or search == all_emoji[e]
    ]
    return results[:25]

  @commands.guild_only()
  @commands.slash_command()
  @commands.default_member_permissions(administrator=True)
  async def reactrole(self, inter:disnake.CommandInteraction, prompt:str):
    """
      Grant members roles whenever they react to a message

      Parameters
      ----------
      prompt: The content of the message that users will react to
    """
    if inter.channel_id in self.drafts:
      await inter.response.send_message(self.babel(inter, 'draft_in_progress'))
      return
    #TODO: save drafts to storage
    self.drafts[inter.channel_id] = self.ReactRoleEditorView(self, inter, prompt)
    await inter.response.send_message(prompt, view=self.drafts[inter.channel_id])
    self.drafts[inter.channel_id].msg = await inter.original_response()
    await inter.followup.send(
      self.babel(inter, 'howto_add_reaction', cmd='/reactrole_add'),
      ephemeral=True
    )


def setup(bot:MerelyBot):
  bot.add_cog(ReactRoles(bot))
