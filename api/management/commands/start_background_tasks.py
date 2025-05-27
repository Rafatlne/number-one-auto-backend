from django.core.management.base import BaseCommand
from loguru import logger


class Command(BaseCommand):
    help = "Start background tasks after database is ready"

    def handle(self, *args, **options):
        try:
            from tasks.fetch_news_task import fetch_news_task
            fetch_news_task(repeat=600)
            logger.success("Background tasks started successfully")
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
