"""
Centralised logger using loguru.
Import `logger` from here everywhere in the project.
"""

import sys
from loguru import logger

logger.remove()                        # remove default stderr sink
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
           "<level>{message}</level>",
    level="INFO",
    colorize=True,
)
logger.add(
    "logs/pipeline.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} — {message}",
)

__all__ = ["logger"]
