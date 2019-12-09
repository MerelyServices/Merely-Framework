import globals
import asyncio
import discord
from discord.ext import commands

class Obsolete(commands.Cog):
	"""Commands that are obsolete."""
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True, no_pm=False, aliases=['join','summon','disconnect','play','pause','ping','settings','lyrics','nowplaying','np','playlists','queue','remove','scsearch','shuffle','skip','forceremove','forceskip','playnext','repeat','loop','skipto','stop','volume','vol'])
	async def music(self, ctx):
		await ctx.message.channel.send(f"to use merely for music, please add the merely music bot!\nhttps://discordapp.com/oauth2/authorize?client_id={globals.musicbuddy}&scope=bot&permissions=0")
	@commands.command(pass_context=True, no_pm=False)
	async def nsfw(self, ctx):
		await ctx.message.channel.send('merely supports nsfw through using the `m/images` command in an nsfw channel.')