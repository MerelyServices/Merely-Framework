"""
  ReactRoles - Adds and takes roles based on a reaction to a message
  In the process of being replaced by EventMsg
"""

from __future__ import annotations

from typing import Union, TYPE_CHECKING
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
  #TODO: notice if the rr prompt is deleted during setup

  # Utility functions

  async def get_roles(self, guild:disnake.Guild, configid:str) -> list[disnake.Role] | None:
    if configid in self.bot.config['reactroles']:
      roleids = [
        int(r) for r in self.bot.config['reactroles'][configid].split(' ')
      ]
      roles:list[disnake.Role] = []
      for roleid in roleids:
        try:
          roles.append(guild.get_role(roleid))
        except Exception as e:
          print("failed to get role for reactrole: "+str(e))
      return roles
    return None

  async def change_roles(
    self,
    member:disnake.Member,
    give:Union[list[disnake.Role], set[disnake.Role]] = [],
    take:Union[list[disnake.Role], set[disnake.Role]] = [],
    reason='reactroles',
    dm=True
  ) -> int:
    # Don't add roles that the member already has
    (give.remove(role) for role in member.roles)
    # Don't take roles that the member already doesn't have
    take = set(take) & set(member.roles)
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

  async def catchup(self, msg:disnake.Message):
    """ Give and take roles as needed to catch up to reality """
    members = await msg.guild.fetch_members().flatten()
    reacts = msg.reactions
    changecount = 0
    pendingchanges: dict[disnake.Member, dict[bool, set[disnake.Role]]]
    pendingchanges = {m: {True: set(), False: set()} for m in members}

    for react in reacts:
      emojiid = react.emoji if type(react.emoji) is str else react.emoji.id
      roleconfid = f"{msg.channel.id}_{msg.id}_{emojiid}_roles"
      if roles := await self.get_roles(msg.guild, roleconfid):
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
    changes = 0
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
      changes += await self.catchup(msg)
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

  @commands.command(aliases=['reactionrole', 'rr', 'reactroles', 'reactionroles'])
  @commands.guild_only()
  async def reactrole(self, ctx:commands.Context, *, prompt:str):
    """react role setup interface"""
    self.bot.cogs['Auth'].admins(ctx.message)

    target = await ctx.reply(prompt)
    tmp = None

    emojis = []
    try:
      while len(emojis) < 10:
        tmp = await ctx.reply(self.bot.babel(ctx, 'reactroles', 'setup1', canstop=len(emojis) > 0))
        reaction, _ = await self.bot.wait_for(
          'reaction_add',
          check=lambda r, u: u == ctx.author and r.message == target,
          timeout=30
        )

        if reaction.emoji not in emojis:
          await target.add_reaction(reaction)
          try:
            await target.remove_reaction(reaction, ctx.author)
          except (disnake.Forbidden, disnake.NotFound):
            pass
          await tmp.delete()

          tmp = await ctx.reply(self.bot.babel(
            ctx, 'reactroles', 'setup2', emoji=str(reaction.emoji)
          ))
          msg = await self.bot.wait_for(
            'message',
            check=(
              lambda m:
              m.channel == ctx.channel and m.author == ctx.author and len(m.role_mentions) > 0
            ),
            timeout=30)
          emojiid = reaction.emoji if isinstance(reaction.emoji, str) else str(reaction.emoji.id)
          roleconfid = f"{ctx.channel.id}_{target.id}_{emojiid}_roles"
          self.bot.config['reactroles'][roleconfid] = ' '.join(
            [str(r.id) for r in msg.role_mentions]
          )
          await tmp.delete()
          await msg.delete()

          emojis.append(reaction)
        else:
          try:
            await target.remove_reaction(reaction, ctx.author)
          except (disnake.Forbidden, disnake.NotFound):
            pass
          await tmp.delete()
          tmp = await ctx.reply(self.bot.babel(ctx, 'reactroles', 'setup2_repeat'))
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
        await ctx.reply(self.bot.babel(ctx, 'reactroles', 'setup_cancel'))
      else:
        try:
          await tmp.delete()
        except (disnake.Forbidden, disnake.NotFound):
          pass
        await ctx.reply(self.bot.babel(ctx, 'reactroles', 'setup_success'))
        self.watching.append(target)
    else:
      await ctx.reply(self.bot.babel(ctx, 'reactroles', 'setup_success'))
      self.watching.append(target)
    self.bot.config.save()


def setup(bot:MerelyBot):
  bot.add_cog(ReactRoles(bot))
