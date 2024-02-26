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
