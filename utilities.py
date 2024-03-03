"""
  Merely Utilities
  Just a modest collection of utility functions that should be useful for multiple bots.
"""


class Utilities:
  def progress_bar(self, value:int, maxval:int, width:int = 20):
    """ Create a progress bar using string manipulation """
    fill = round(((value/maxval)*(width*2))) / 2
    half = fill % 1
    return int(fill) * '█' + ('▒' if half else '') + (width - int(fill) - (1 if half else 0))*'░'

  def truncate(self, string:str, maxlen:int = 80) -> str:
    """ Auto-trim strings and add ellipsis if needed """
    n = maxlen - 3 if len(string) > maxlen else maxlen
    return string[:n] + ('...' if len(string) > maxlen else '')
