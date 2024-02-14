"""
  ReactRoles - Adds and takes roles based on a reaction to a message
  In the process of being replaced by EventMsg
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio
import disnake
from disnake.ext import commands

if TYPE_CHECKING:
  from ..main import MerelyBot


class ReactRoles(commands.Cog):
  """allows admins to set up messages where reacting grants users roles"""
  def __init__(self, bot:MerelyBot):
    self.bot = bot
    if not bot.config.getboolean('extensions', 'auth', fallback=False):
      raise AssertionError("'auth' must be enabled to use 'reactroles'")
    if not bot.config.getboolean('extensions', 'help', fallback=False):
      print(Warning("'help' is a recommended extension for 'reactroles'"))
    # ensure config file has required data
    if not bot.config.has_section('reactroles'):
      bot.config.add_section('reactroles')
    self.watching:list[disnake.Message] = []

  #TODO: make it possible for admins to add more reaction roles or delete them later

  # Utility functions

  async def get_roles(self, guild:disnake.Guild, configid:str) -> set[disnake.Role] | None:
    if configid in self.bot.config['reactroles']:
      roleids = [
        int(r) for r in self.bot.config['reactroles'][configid].split(' ')
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
      if len(give)+len(take) > 0 and dm:
        await member.send(self.bot.babel(
          member,
          'reactroles',
          'role_change',
          taken=', '.join((role.name for role in take)) if take else False,
          given=', '.join((role.name for role in give)) if give else False,
          server=member.guild.name
        ))
    except disnake.HTTPException:
      pass
    return len(give)+len(take)

  async def catchup(self, messages:list[disnake.Message]):
    """ Give and take roles as needed to catch up to reality """
    changecount = 0
    guilds = set(m.guild for m in messages)
    for guild in guilds:
      members = await guild.fetch_members().flatten()
      pendingchanges: dict[disnake.Member, dict[bool, set[disnake.Role]]]
      pendingchanges = {m: {True: set(), False: set()} for m in members}

      for msg in messages:
        if msg.guild == guild:
          for react in msg.reactions:
            emojiid = react.emoji if type(react.emoji) is str else react.emoji.id
            roleconfid = f"{msg.channel.id}_{msg.id}_{emojiid}_roles"
            if roles := await self.get_roles(guild, roleconfid):
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

          for member in members:
            give = pendingchanges[member][True].difference(pendingchanges[member][False])
            take = pendingchanges[member][False].difference(pendingchanges[member][False])
            changecount += await self.change_roles(member, give, take, 'reactroles catchup')

    return changecount

  # Events

  @commands.Cog.listener("on_ready")
  async def fetch_tracking_messages(self):
    """ Request the message once so we'll be notified if reactions change """
    search = [k for k in self.bot.config['reactroles'].keys()]
    print("reactroles catchup started")
    for chid,msgid in set([(rr.split('_')[0], rr.split('_')[1]) for rr in search]):
      msg: disnake.Message
      try:
        ch = await self.bot.fetch_channel(chid)
        msg = await ch.fetch_message(msgid)
      except Exception as e:
        print(f"failed to get reactionrole message {msgid} from channel {chid}. {e}")
        continue
      self.watching.append(msg)
    changes = await self.catchup(self.watching)
    print("reactroles catchup ended. Delta: ", changes)

  @commands.Cog.listener("on_message_delete")
  async def revoke_tracking_message(self, message):
    """ Remove message from config so it won't attempt to load it again """
    if message in self.watching:
      matches = [
        k for k in self.bot.config['reactroles'].keys() if k.split('_')[1] == str(message.id)
      ]
      for k in matches:
        self.bot.config.remove_option('reactroles',k)
      self.watching.remove(message)

  @commands.Cog.listener("on_raw_reaction_add")
  async def reactrole_add(self, data:disnake.RawReactionActionEvent):
    """ Grant the user their role """
    if isinstance(data.member, disnake.Member):
      emojiid = data.emoji if data.emoji.is_unicode_emoji() else data.emoji.id
      roleconfid = f"{data.channel_id}_{data.message_id}_{emojiid}_roles"
      if roles := await self.get_roles(data.member.guild, roleconfid):
        await self.change_roles(data.member, give=roles)

  @commands.Cog.listener("on_raw_reaction_remove")
  async def reactrole_remove(self, data:disnake.RawReactionActionEvent):
    """ Take back roles """
    if data.guild_id:
      member = await self.bot.get_guild(data.guild_id).getch_member(data.user_id)
      emojiid = data.emoji if data.emoji.is_unicode_emoji() else data.emoji.id
      roleconfid = f"{data.channel_id}_{data.message_id}_{emojiid}_roles"
      if roles := await self.get_roles(member.guild, roleconfid):
        await self.change_roles(member, take=roles)

  # Commands

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
    self.bot.cogs['Auth'].admins(inter.message)

    await inter.response.send_message(prompt)
    target = await inter.original_response()
    tmp = None

    emojis = []
    try:
      while len(emojis) < 10:
        tmp = await inter.channel.send(
          self.bot.babel(inter, 'reactroles', 'setup1', canstop=len(emojis) > 0)
        )
        reaction, _ = await self.bot.wait_for(
          'reaction_add',
          check=lambda r, u: u == inter.author and r.message == target,
          timeout=30
        )

        if reaction.emoji not in emojis:
          await target.add_reaction(reaction)
          try:
            await target.remove_reaction(reaction, inter.author)
          except (disnake.Forbidden, disnake.NotFound):
            pass
          await tmp.delete()

          tmp = await inter.channel.send(self.bot.babel(
            inter, 'reactroles', 'setup2', emoji=str(reaction.emoji)
          ))
          msg = await self.bot.wait_for(
            'message',
            check=(
              lambda m:
              m.channel == inter.channel and m.author == inter.author and len(m.role_mentions) > 0
            ),
            timeout=30)
          emojiid = reaction.emoji if isinstance(reaction.emoji, str) else str(reaction.emoji.id)
          roleconfid = f"{inter.channel.id}_{target.id}_{emojiid}_roles"
          self.bot.config['reactroles'][roleconfid] = ' '.join(
            [str(r.id) for r in msg.role_mentions]
          )
          await tmp.delete()
          await msg.delete()

          emojis.append(reaction)
        else:
          try:
            await target.remove_reaction(reaction, inter.author)
          except (disnake.Forbidden, disnake.NotFound):
            pass
          await tmp.delete()
          tmp = await inter.channel.send(self.bot.babel(inter, 'reactroles', 'setup2_repeat'))
          await asyncio.sleep(5)
          await tmp.delete()

    except asyncio.TimeoutError:
      if len(emojis) == 0:
        try:
          await target.delete()
          if tmp is not None:
            await tmp.delete()
        except (disnake.Forbidden, disnake.NotFound):
          pass
        await inter.channel.send(self.bot.babel(inter, 'reactroles', 'setup_cancel'))
      else:
        try:
          await tmp.delete()
        except (disnake.Forbidden, disnake.NotFound):
          pass
        await inter.response.send_message(self.bot.babel(inter, 'reactroles', 'setup_success'))
        self.watching.append(target)
    else:
      await inter.response.send_message(self.bot.babel(inter, 'reactroles', 'setup_success'))
      self.watching.append(target)
    self.bot.config.save()


def setup(bot:MerelyBot):
  bot.add_cog(ReactRoles(bot))
