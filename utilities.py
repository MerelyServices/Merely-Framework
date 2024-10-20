"""
  Merely Utilities
  Just a modest collection of utility functions that should be useful for multiple bots.
"""

from typing import Callable
import discord


class Utilities:
  def progress_bar(self, value:int, maxval:int, width:int = 20):
    """ Create a progress bar using string manipulation """
    fill = round(((value/max(maxval,1))*(width*2))) / 2
    half = fill % 1
    return int(fill) * '█' + ('▒' if half else '') + (width - int(fill) - (1 if half else 0))*'░'

  def truncate(self, string, maxlen:int = 80) -> str:
    """ Auto-trim strings, remove newlines, and add ellipsis if needed """
    _str = str(string).replace('\n', ' ')
    n = maxlen - 3 if len(_str) > maxlen else maxlen
    return _str[:n] + ('...' if len(_str) > maxlen else '')

  class CallbackButton(discord.ui.Button):
    """ Modified Button which can have a pre-defined callback function """
    def __init__(self, callback:Callable[[discord.Interaction], None], **kwargs) -> None:
      super().__init__(**kwargs)
      self.callback = callback

  class CallbackSelect(discord.ui.Select):
    """ Modified Select which can have a pre-defined callback function """
    def __init__(self, callback:Callable[[discord.Interaction], None], **kwargs) -> None:
      super().__init__(**kwargs)
      self.callback = callback
