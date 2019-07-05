import asyncio
import discord
from discord.ext import commands

class Obsolete(commands.Cog):
	"""Commands that are obsolete."""
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True, no_pm=False, aliases=['join','summon','disconnect','play','pause'])
	async def music(self, ctx):
		await ctx.message.channel.send('merely no longer provides music functionality. we recommend https://fredboat.com/ instead.')
	@commands.command(pass_context=True, no_pm=False)
	async def nsfw(self, ctx):
		await ctx.message.channel.send('merely supports nsfw through using the `m/images` command in an nsfw channel.')