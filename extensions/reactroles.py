import discord, asyncio
from discord.ext import commands

class ReactRoles(commands.cog.Cog):
  """allows admins to set up messages where reacting grants users roles"""
  def __init__(self, bot : commands.Bot):
    self.bot = bot
    if not bot.config.getboolean('extensions', 'auth', fallback=False):
      raise Exception("'auth' must be enabled to use 'reactroles'")
    if not bot.config.getboolean('extensions', 'help', fallback=False):
      print(Warning("'help' is a recommended extension for 'reactroles'"))
    self.auth = bot.cogs['Auth']
    # ensure config file has required data
    if not bot.config.has_section('reactroles'):
      bot.config.add_section('reactroles')
    msglist = 'list[discord.abc.Messageable]'
    self.watching : msglist = []

  @commands.Cog.listener("on_ready")
  async def fetch_tracking_messages(self):
    search = [k for k in self.bot.config['reactroles'].keys()]
    for chid,msgid in set([(rr.split('_')[0], rr.split('_')[1]) for rr in search]):
      try:
        ch = await self.bot.fetch_channel(chid)
        msg = await ch.fetch_message(msgid)
        self.watching.append(msg)
      except Exception as e:
        print(f"failed to get reactionrole message {msgid} from channel {chid}, deleting config. {e}")
        [self.bot.config.remove_option('reactroles', k) for k in search]
    self.bot.config.save()
    await self.catchup()

  @commands.Cog.listener("on_message_delete")
  async def revoke_tracking_message(self, message):
    if message in self.watching:
      matches = [k for k in self.bot.config['reactroles'].keys() if k.split('_')[1] == str(message.id)]
      [self.bot.config.remove_option('reactroles',k) for k in matches]
      #TODO: (low priority) maybe remove deleted message from self.watching?

  @commands.Cog.listener("on_reaction_add")
  async def reactrole_add(self, reaction, member):
    print('add')
    if isinstance(member, discord.Member):
      emojiid = reaction.emoji if isinstance(reaction.emoji, str) else str(reaction.emoji.id)
      if f"{reaction.message.channel.id}_{reaction.message.id}_{emojiid}_roles" in self.bot.config['reactroles']:
        roleids = [int(r) for r in self.bot.config['reactroles'][f"{reaction.message.channel.id}_{reaction.message.id}_{emojiid}_roles"].split(' ')]
        roles = []
        for roleid in roleids:
          try:
            roles.append(member.guild.get_role(roleid))
          except Exception as e:
            print("failed to get role for reactrole: "+str(e))
        await member.add_roles(*roles, reason='reactroles')
      else:
        print('config miss')

  @commands.Cog.listener("on_reaction_remove")
  async def reactrole_remove(self, reaction, member):
    print('remove')
    if isinstance(member, discord.Member):
      emojiid = reaction.emoji if isinstance(reaction.emoji, str) else str(reaction.emoji.id)
      if f"{reaction.message.channel.id}_{reaction.message.id}_{emojiid}_roles" in self.bot.config['reactroles']:
        roleids = [int(r) for r in self.bot.config['reactroles'][f"{reaction.message.channel.id}_{reaction.message.id}_{emojiid}_roles"].split(' ')]
        roles = []
        for roleid in roleids:
          try:
            roles.append(member.guild.get_role(roleid))
          except Exception as e:
            print("failed to get role for reactrole: "+str(e))
        await member.remove_roles(*roles, reason='reactroles')
      else:
        print('config miss')
  
  async def catchup(self):
    #TODO: give and take roles as needed to catch up to reality
    pass

  @commands.command(aliases=['reactionrole', 'rr', 'reactroles', 'reactionroles'])
  @commands.guild_only()
  async def reactrole(self, ctx : commands.Context, *, prompt):
    """reactrole (prompt)
    creates a message with your given prompt for reactions. each react can be associated with roles.
    roles will be given to any users that react with a given reaction."""
    self.auth.admins(ctx)

    target = await ctx.send(prompt)

    emojis = []
    try:
      while len(emojis) < 10:
        tmp = await ctx.send("react to the prompt to add a reactionrole." + (" *don't react to finish.*" if len(emojis) > 0 else ''))
        reaction, _ = await self.bot.wait_for('reaction_add', check=lambda r, u: u==ctx.author and r.message == target, timeout=30)

        if reaction.emoji not in emojis:
          await target.add_reaction(reaction)
          try:
            await target.remove_reaction(reaction, ctx.author)
          except:
            pass
          await tmp.delete()

          tmp = await ctx.send("mention role(s) to add them to "+str(reaction.emoji))
          msg = await self.bot.wait_for('message', check=lambda m: m.channel == ctx.channel and m.author == ctx.author and len(m.role_mentions) > 0, timeout=30)
          emojiid = reaction.emoji if isinstance(reaction.emoji, str) else str(reaction.emoji.id)
          self.bot.config['reactroles'][f"{ctx.channel.id}_{target.id}_{emojiid}_roles"] = ' '.join([str(r.id) for r in msg.role_mentions])
          await tmp.delete()
          await msg.delete()
          
          emojis.append(reaction)
        else:
          try:
            await target.remove_reaction(reaction, ctx.author)
          except:
            pass
          await tmp.delete()
          tmp = await ctx.send("**this emoji has already been given roles.**")
          await asyncio.sleep(5)
          await tmp.delete()

    except asyncio.TimeoutError:
      if len(emojis) == 0:
        try:
          await target.delete()
        except:
          pass
        await ctx.send("canceled reactionroles setup *(timeout after each instruction is 30 seconds)*")
      else:
        try:
          await tmp.delete()
        except:
          pass
        await ctx.send("reactionroles setup complete! delete the prompt at any time to undo.")
    else:
      await ctx.send("reactionroles setup complete! delete the prompt at any time to undo.")
    self.bot.config.save()


def setup(bot):
  bot.add_cog(ReactRoles(bot))