"""
  Download - Convert links to media into video files
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands
import subprocess, os, glob, asyncio, shlex
from urllib.parse import urlparse, ParseResult

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy


# Utility functions

def uri_validator(x):
    try:
        result:ParseResult = urlparse(x)
        return all([result.scheme, result.netloc])
    except AttributeError:
        return False


class Example(commands.Cog):
  """ Adds an echo command and logs new members """
  SCOPE = 'download'

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> str:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    self.runtime_counter = 0

    # check yt-dlp is installed
    try:
      out = subprocess.check_output(['yt-dlp', '--version'])
    except FileNotFoundError:
      raise Exception("Install yt-dlp on your system in order to use the download module.")
    else:
      print("    - yt-dlp version installed is", out[:-1].decode())

    # ensure tmp path exists and is empty
    os.makedirs('tmp', exist_ok=True)
    files = glob.glob(os.path.join('tmp', '*'))
    for f in files:
      os.remove(f)

  @app_commands.command()
  @app_commands.describe(
    media_url="A link to almost any web page with a video. Doesn't work if payment is required."
  )
  @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
  @app_commands.allowed_installs(guilds=True, users=True)
  @commands.has_permissions(send_messages=True)
  async def download(self, inter:discord.Interaction, media_url:str):
    """
      Download a video file and send it back as a message
    """
    if not uri_validator(media_url):
      await inter.response.send_message("Media URL appears to be invalid. Not downloading.")
      return
    await inter.response.defer(thinking=True)
    filenumber = self.runtime_counter
    self.runtime_counter += 1
    dlp = await asyncio.create_subprocess_shell(' '.join((
      'yt-dlp',
      '--max-filesize', '25M',
      '--no-playlist',
      '--max-downloads', '1',
      '--limit-rate', '2M',
      '--output', f'tmp/{filenumber}.mp4',
      '--quiet',
      '--no-warnings',
      '-S', '"+codec:h264,res:720,fps"',
      shlex.quote(media_url)
    )), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    logs = ''
    if stdout := await dlp.stdout.read():
      logs += '```'+stdout.decode()+'```\n'
    if stderr := await dlp.stderr.read():
      logs += '```'+stderr.decode()+'```\n'
    filepath = os.path.join('tmp', f'{filenumber}.mp4')
    if os.path.exists(filepath):
      await inter.edit_original_response(attachments=(discord.File(filepath),))
    else:
      await inter.edit_original_response("Download failed;\n" + logs)


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Example(bot))
