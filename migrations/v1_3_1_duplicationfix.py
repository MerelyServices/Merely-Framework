"""
  This script fixes duplicated announcement subscriptions
  The announce module has been making these in error, fixed in v1.3.1
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from config import Config


def process_list(data:str) -> str:
  return ','.join(list(dict.fromkeys(data.split(',')))) + ','


def migrate(config:Config):
  print(" - Removing duplicate announcement subscriptions...")

  config['announce']['dm_subscription'] = process_list(config['announce']['dm_subscription'])
  config['announce']['subscription_history'] = process_list(
    config['announce']['subscription_history']
  )

  print(" - Removing duplicate announcement subscriptions complete!")
