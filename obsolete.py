import globals
import asyncio
import discord
from discord.ext import commands

class Obsolete(commands.Cog):
	"""Commands that are obsolete."""
	def __init__(self, bot):
		self.bot = bot

	@commands.command(no_pm=False, aliases=['join','summon','disconnect','play','pause','ping','settings','lyrics','nowplaying','np','playlists','queue','remove','scsearch','shuffle','skip','forceremove','forceskip','playnext','repeat','loop','skipto','stop','volume','vol'])
	async def music(self, ctx):
		if globals.musicbuddy:
			await ctx.send(f"to use {globals.name} for music, please add the {globals.name} music bot!\nhttps://discordapp.com/oauth2/authorize?client_id={globals.musicbuddy}&scope=bot&permissions=0")
	@commands.command(no_pm=False)
	async def nsfw(self, ctx):
		await ctx.send(f"{globals.name} supports nsfw through using the `{globals.prefix_short}images` command in an nsfw channel.")