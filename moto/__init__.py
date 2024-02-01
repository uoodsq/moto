"""
Used to manage and pull stats from a Motorola MB8600 modem (and possibly others).
"""

__version__ = "1.0"

import logging

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
