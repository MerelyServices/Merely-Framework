"""
  Poll - Hold community polls
  Features: Tracks time before, during, and after a poll. Recovers from restarts.
  Recommended cogs: Help, Error
"""

from __future__ import annotations

from time import time
import re
from typing import Optional, TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import tasks, commands

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


class LivePoll():
  """
    LivePoll stores the state of one ongoing poll

    An ongoing poll is defined as any poll which is occasionally updating on Discord.
  """
  parent:Poll
  title:str
  answers:list[str]
  votes:list[int]
  expiry:int
  expired:bool = False
  message:discord.Message

  EMOJIS = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']

  def __init__(self, parent:Poll):
    self.parent = parent

  @property
  def counter(self) -> int:
    return int(self.expiry - time())

  def get_expiry(self):
    configkey = f'{self.message.channel.id}_{self.message.id}_expiry'
    if configkey in self.parent.config:
      self.expiry = int(self.parent.config[configkey])
    else:
      self.expiry = int(self.parent.config[configkey+'_expired'])
      self.expired = True

  def create(self, title:str, answers:list[str], votes:list[int], expiry:int):
    """ Creates a new poll based on user input """
    self.title = title
    self.answers = answers
    self.votes = votes
    self.expiry = int(expiry)

  def save(self, message:discord.Message):
    """ Writes poll to config and stores message in memory """
    self.message = message
    configkey = f'{message.channel.id}_{message.id}_expiry'+('_expired' if self.expired else '')
    self.parent.config[configkey] = str(self.expiry)
    self.parent.bot.config.save()

  def load(self, message:discord.Message):
    """ Loads poll from config and stores message in memory """
    self.message = message
    self.get_expiry()

  def remove(self, save=True):
    """ Clears poll from config - from here, this object can safely be dereferenced """
    configkey = f'{self.message.channel.id}_{self.message.id}_expiry' +\
                ('_expired' if self.expired else '')
    self.parent.config.pop(configkey)
    if save:
      self.parent.bot.config.save()

  def expiry_to_time(self, guild:discord.Guild, precisionlimit:int = 1) -> str:
    """ Converts countdown seconds into a nicely formatted sentence """
    # Import current locale strings
    TIMENAMES = self.parent.babel(guild, 'timenames').split(',')
    assert len(TIMENAMES) == 7
    TIMEPLURALS = self.parent.babel(guild, 'timeplurals').split(',')
    assert len(TIMEPLURALS) == 7
    TIMENUMFORMAT = self.parent.babel(guild, 'time_number_format')
    assert TIMENUMFORMAT.find('{number}') >= 0 and TIMENUMFORMAT.find('{name}') >= 0

    if self.counter == 0:
      return self.parent.babel(guild, 'present')

    MULTIPLIERS = [31449600, 2419200, 604800, 86400, 3600, 60,    1]
    #              year      month    week    day    hour  minute second

    times = []
    workingnumber = abs(self.counter)

    for multiplier,ni in tuple(zip(MULTIPLIERS, range(len(MULTIPLIERS)))):
      # ni is the name index, used to map TIMENAMES and TIMEPLURALS
      if workingnumber >= multiplier:
        product = workingnumber // multiplier
        if product > 0:
          times.append(TIMENUMFORMAT.format(
            number=str(product),
            name=(TIMEPLURALS[ni] if product != 1 else TIMENAMES[ni])
          ))
          workingnumber = workingnumber % multiplier
          if len(times) >= 2:
            break
      if ni >= precisionlimit:
        break

    timelist = self.parent.bot.babel.string_list(guild, times)
    if timelist == '':
      #BABEL: near_past,near_future
      return self.parent.babel(guild, 'near_past' if self.counter < 0 else 'near_future')
    else:
      #BABEL: far_past,far_future
      return self.parent.babel(
        guild,
        'far_past' if self.counter < 0 else 'far_future',
        timelist=timelist
      )

  def generate_embed(self, guild:discord.Guild):
    """ Generates a poll embed based on the object data """
    embed = discord.Embed(title=self.title)
    if self.counter > 0:
      # Counting down
      if self.counter > 60:
        embed.description = f"⏳ {self.expiry_to_time(guild, 5)}" # 5 = count minutes
      else:
        embed.description = f"⌛ {self.expiry_to_time(guild, 6)}" # 6 = count seconds
    elif self.counter <= -604800:
      # Expired
      embed.description = f"⌛ {self.parent.babel(guild, 'inf_past')}"
    else:
      # Poll has finished, counting time since
      embed.description = f"⌛ {self.expiry_to_time(guild, 4 if self.counter > -86400 else 2)}"
      #                                                    4 = count hours,  3 = count days
    votemax = max(self.votes + [1])
    index = 0
    for answer,vote in tuple(zip(self.answers,self.votes)):
      embed.add_field(
        name=f'{self.EMOJIS[index]} {answer}:',
        value=f'{self.parent.bot.utilities.progress_bar(vote,votemax)} ({vote})',
        inline=False
      )
      index += 1
    if not self.expired:
      embed.set_footer(text=self.parent.babel(guild, 'vote_cta', multichoice=True))
    return embed

  async def add_reacts(self):
    for i in range(len(self.answers)):
      await self.message.add_reaction(self.EMOJIS[i])

  async def redraw(self):
    """ Recover data from the embed, count reactions, then regenerate the embed """
    if not hasattr(self, 'title'):
      self.title = self.message.embeds[0].title
      self.answers = [f.name[4:-1] for f in self.message.embeds[0].fields]
      if self.expired:
        self.votes = [
          int(re.match(r'.*\((\d+)\)', f.value).group(1)) for f in self.message.embeds[0].fields
        ]
      else:
        self.votes = [0 for _ in self.answers]
        for react in self.message.reactions:
          if str(react.emoji) in self.EMOJIS:
            self.votes[self.EMOJIS.index(str(react.emoji))] = react.count-1
    embed = self.generate_embed(self.message.guild)
    await self.message.edit(embed=embed)

  async def finish(self):
    """ Announce the winner of the poll """
    self.remove(False)
    self.expired = True
    self.save(self.message)
    await self.redraw()
    winners = []
    votemax = max(self.votes + [1])
    if votemax > 0:
      for answer,votecount in tuple(zip(self.answers, self.votes)):
        if votecount == votemax:
          winners.append(answer)

    if len(winners) == 0:
      await self.message.channel.send(
        self.parent.babel(self.message.guild, 'no_winner', title=self.title),
        reference=self.message
      )
    elif len(winners) == 1:
      await self.message.channel.send(
        self.parent.babel(self.message.guild, 'one_winner', title=self.title, winner=winners[0]),
        reference=self.message
      )
    else:
      winnerstring = self.parent.bot.babel.string_list(self.message.guild, winners)
      await self.message.channel.send(
        self.parent.babel(self.message.guild, 'multiple_winners',
                          title=self.title,
                          num=len(winners),
                          winners=winnerstring),
        reference=self.message
      )
    await self.redraw()


class Poll(commands.Cog):
  """
    Poll is an almost stateless poll extension for discord bots
    This improved poll handles votes even if the bot goes offline
    Also keeps the countdown timer up to date for a week after expiry
  """
  SCOPE = 'poll'

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  livepolls: dict[int, LivePoll] = {}
  poll_tick_timer: tasks.Loop
  current_poll_timer: tasks.Loop
  old_poll_timer: tasks.Loop
  ancient_poll_timer: tasks.Loop

  def __init__(self, bot:MerelyBot):
    self.bot = bot

    # ensure config file has required data
    if not bot.config.has_section(self.SCOPE):
      bot.config.add_section(self.SCOPE)

  def cog_unload(self) -> None:
    # stop timers, otherwise old code continues running
    self.poll_tick_timer.cancel()
    self.current_poll_timer.cancel()
    self.old_poll_timer.cancel()
    self.ancient_poll_timer.cancel()
    self.livepolls = {}

  @commands.Cog.listener('on_connect')
  async def validate_cache(self):
    save = False
    for key in self.config:
      keysplit = key.split('_')
      if len(keysplit) >= 2:
        channel_id, message_id = (int(k) for k in keysplit[:2])
        if message_id not in self.livepolls:
          try:
            channel = await self.bot.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)
          except (discord.NotFound, discord.Forbidden):
            self.config.pop(key)
            save = True
            continue

          self.livepolls[message_id] = LivePoll(self)
          self.livepolls[message_id].load(message)
          await self.livepolls[message_id].redraw()
    if save:
      self.bot.config.save()

    # start timers
    self.poll_tick_timer.start()
    self.current_poll_timer.start()
    self.old_poll_timer.start()
    self.ancient_poll_timer.start()

  @commands.Cog.listener('on_raw_reaction_add')
  @commands.Cog.listener('on_raw_reaction_remove')
  @commands.Cog.listener('on_raw_reaction_clear')
  @commands.Cog.listener('on_raw_reaction_clear_emoji')
  async def poll_react(
    self,
    e:(
      discord.RawReactionActionEvent |
      discord.RawReactionClearEvent |
      discord.RawReactionClearEmojiEvent
    )
  ):
    """ Handle changes to the reaction list of a poll """
    if e.message_id in self.livepolls and\
       (not hasattr(e, 'user_id') or e.user_id != self.bot.user.id):
      poll = self.livepolls[e.message_id]
      if poll.expiry > time():
        if isinstance(e, discord.RawReactionActionEvent):
          poll.votes[poll.EMOJIS.index(str(e.emoji))] += 1 if e.event_type == 'REACTION_ADD' else -1
        elif isinstance(e, discord.RawReactionClearEmojiEvent):
          poll.votes[poll.EMOJIS.index(str(e.emoji))] = 0
        else:
          poll.votes = [0 for _ in poll.answers]
          await poll.add_reacts()
        if poll.expiry > time() + 60:
          await poll.redraw()

  @commands.Cog.listener('on_message_delete')
  async def poll_delete(self, message:discord.Message):
    if message.id in self.livepolls:
      self.livepolls[message.id].remove()
      self.livepolls.pop(message.id)

  @tasks.loop(seconds=1)
  async def poll_tick_timer(self):
    """ Polls that have less than a minute to go count down every second """
    poll: LivePoll
    iters = len(self.livepolls)
    for i in range(iters):
      if i < len(self.livepolls):
        poll = self.livepolls[list(self.livepolls.keys())[i]]
      else:
        continue
      if not poll.expired and poll.expiry <= time() + 60:
        if poll.expiry > time():
          await poll.redraw()
        else:
          await poll.finish()

  @tasks.loop(minutes=1)
  async def current_poll_timer(self):
    """ Polls that haven't expired yet count down every minute """
    poll: LivePoll
    iters = len(self.livepolls)
    for i in range(iters):
      if i < len(self.livepolls):
        poll = self.livepolls[list(self.livepolls.keys())[i]]
      else:
        continue
      if not poll.expired and poll.expiry > time() + 60:
          await poll.redraw()

  @tasks.loop(hours=1)
  async def old_poll_timer(self):
    """ Polls that expired within the last 24 hours count once an hour """
    poll: LivePoll
    iters = len(self.livepolls)
    for i in range(iters):
      if i < len(self.livepolls):
        poll = self.livepolls[list(self.livepolls.keys())[i]]
      else:
        continue
      if poll.expired and poll.expiry > time() - (60 * 60 * 24):
        await poll.redraw()

  @tasks.loop(hours=24)
  async def ancient_poll_timer(self):
    """
      Polls that expired more than 24 hours ago count once a day
      After a week, they are deleted from the config
    """
    poll: LivePoll
    iters = len(self.livepolls)
    for i in range(iters):
      if i < len(self.livepolls):
        poll = self.livepolls[list(self.livepolls.keys())[i]]
      else:
        continue
      if poll.expired and poll.expiry <= time() - (60 * 60 * 24):
        await poll.redraw()
        if poll.expiry < time() - (60 * 60 * 24 * 7):
          self.livepolls.pop(poll.message.id)
          poll.remove()

  @app_commands.command()
  @commands.bot_has_permissions(read_messages=True, send_messages=True, add_reactions=True)
  @app_commands.guild_only()
  async def poll(
    self,
    inter:discord.Interaction,
    title:str,
    answer1:str,
    answer2:str,
    answer3:Optional[str] = None,
    answer4:Optional[str] = None,
    answer5:Optional[str] = None,
    answer6:Optional[str] = None,
    answer7:Optional[str] = None,
    answer8:Optional[str] = None,
    answer9:Optional[str] = None,
    answer10:Optional[str] = None,
    expiry_days:Optional[int] = 0,
    expiry_hours:Optional[int] = 0,
    expiry_minutes:Optional[int] = 0,
    expiry_seconds:Optional[int] = 0
  ):
    """
      Creates a poll with up to 10 options and an expiry time

      Parameters
      ----------
      title: The subject of the poll, appears above the options
      answer1: Option A. Required
      answer2: Option B. Required
      answer3: Option C. Not required.
      answer4: Option D. Not required.
      answer5: Option E. Not required.
      answer6: Option F. Not required.
      answer7: Option G. Not required.
      answer8: Option H. Not required.
      answer9: Option I. Not required.
      answer10: Option J. Not required.
      expiry_days: Number of days until the poll expires. Summed with other expiry fields.
      expiry_hours: Number of hours until the poll expires. Summed with other expiry fields.
      expiry_minutes: Number of minutes until the poll expires. Summed with other expiry fields.
      expiry_seconds: Number of seconds until the poll expires. Summed with other expiry fields.
    """
    # Remove duplicate answers and unset answers while preserving the specified order
    raw_answers = [
      answer1, answer2, answer3, answer4, answer5, answer6, answer7, answer8, answer9, answer10
    ]
    answers = []
    for ans in raw_answers:
      if ans is not None and ans not in answers:
        answers.append(ans)

    expiry = expiry_seconds + (expiry_minutes * 60) + (expiry_hours * 3600) + (expiry_days * 86400)
    if expiry == 0:
      expiry = 300
    poll = LivePoll(self)
    poll.create(title, answers, [0]*len(answers), time() + expiry)

    embed = poll.generate_embed(inter.guild)
    announce = self.babel(inter.guild, 'poll_created', author=inter.user.mention)
    await inter.response.send_message(announce, embed=embed)
    message = await inter.original_response()

    self.livepolls[message.id] = poll
    poll.save(message)
    await poll.add_reacts()


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Poll(bot))
