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


class Download(commands.Cog):
  """ Adds an echo command and logs new members """
  SCOPE = 'download'

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: str | bool) -> str:
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

  @app_commands.command(
    name=app_commands.locale_str('download', scope=SCOPE),
    description=app_commands.locale_str('download_desc', scope=SCOPE)
  )
  @app_commands.describe(
    media_url=app_commands.locale_str('download_media_url', scope=SCOPE)
  )
  @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
  @app_commands.allowed_installs(guilds=True, users=True)
  @commands.has_permissions(send_messages=True)
  async def download(self, inter:discord.Interaction, media_url:str):
    """
      Download a video file and send it back as a message
    """
    if not uri_validator(media_url):
      await inter.response.send_message(self.babel(inter, 'invalid_url'))
      return
    await inter.response.defer(thinking=True)
    filenumber = self.runtime_counter
    self.runtime_counter += 1
    dlp = await asyncio.create_subprocess_shell(' '.join((
      'yt-dlp',
      '--format', '"bestvideo[filesize<=9M]+bestaudio[filesize<=2M]/best[filesize<=10M]"'
      '--max-filesize', '10M',
      '--no-playlist',
      '--max-downloads', '2',
      '--limit-rate', '1M',
      '--output', f'tmp/{filenumber}.mp4',
      '--no-warnings',
      '--format-sort', '"+codec:h264,fps"',
      shlex.quote(media_url)
    )), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    logs = ''
    if stderr := await dlp.stderr.read():
      logs = '```'+stderr.decode()+'```\n'
    elif stdout := await dlp.stdout.read():
      logs = '```'+stdout.decode()+'```\n'
    filepath = os.path.join('tmp', f'{filenumber}.mp4')
    if os.path.exists(filepath):
      if os.path.getsize(filepath) > 10_000_000: # 10MB discord limit
        await inter.edit_original_response(content=self.babel(inter, 'too_large'))
        return
      await inter.edit_original_response(attachments=(discord.File(filepath),))
    else:
      await inter.edit_original_response(content=self.babel(inter, 'failed', log=logs))


async def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  await bot.add_cog(Download(bot))
