from background_task import background
from django.utils import timezone
from loguru import logger

from api.management.commands.fetch_news import Command


@background(schedule=10)
def fetch_news_task():
    logger.info(f"Running scheduled news fetch task at {timezone.now()}")

    try:
        cmd = Command()
        cmd.handle()
    except Exception as e:
        logger.error(f"Error running news fetch task: {e}")

    logger.info(f"Scheduled news fetch task completed at {timezone.now()}")
