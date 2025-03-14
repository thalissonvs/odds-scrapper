"""
Logging and application settings configuration.

This module configures the Loguru logger with appropriate formatting,
log rotation, and log levels for the application.
"""

import sys
from pathlib import Path

from loguru import logger

BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)


logger.remove()

logger.add(
    sys.stderr,
    format=(
        '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> '
        '| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
        '<level>{message}</level>'
    ),
    level='INFO',
    colorize=True,
)

logger.add(
    LOGS_DIR / 'app.log',
    format='{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}',
    level='DEBUG',
    rotation='10 MB',
    retention='1 month',
    compression='zip',
    backtrace=True,
    diagnose=True,
)

APP_NAME = 'odds_scraper'
SCRAPER_INTERVAL_SECONDS = 10
USER_AGENT_ROTATION = True

logger = logger.bind(app_name=APP_NAME)
logger.info(f'Starting {APP_NAME}')


def get_logger(name=None):
    """Get a configured logger instance with context.

    Args:
        name (str, optional): Name to bind to the logger context. Defaults to None.

    Returns:
        loguru.Logger: Configured logger instance
    """
    if name:
        return logger.bind(context=name)
    return logger
