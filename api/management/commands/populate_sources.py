from loguru import logger
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import IntegrityError
from api.models import Country, Source

NEWSAPI_SOURCES_ENDPOINT = "https://newsapi.org/v2/sources"


class Command(BaseCommand):
    help = "Populates the Source model by fetching sources from NewsAPI for each country in the database."

    def handle(self, *args, **options):
        logger.info("Starting to populate sources...")

        if not settings.NEWSAPI_KEY:
            logger.error("NEWSAPI_KEY not configured in Django settings.")
            return

        countries = Country.objects.all()
        if not countries.exists():
            logger.warning(
                "No countries found in the database. Please populate countries first."
            )
            return

        total_sources_added = 0
        total_sources_processed_existing = 0

        for db_country in countries:
            params = {"country": db_country.code, "apiKey": settings.NEWSAPI_KEY}

            try:
                response = requests.get(
                    NEWSAPI_SOURCES_ENDPOINT, params=params, timeout=20
                )
                logger.info(f"Called URL for {db_country.code}: {response.url}")
                response.raise_for_status()

                api_response_data = response.json()
                api_sources = api_response_data.get("sources", [])

                if not api_sources:
                    continue

                for source_data in api_sources:
                    api_id = source_data.get("id")
                    if not api_id:
                        continue

                    defaults = {
                        "name": source_data.get("name", ""),
                        "description": source_data.get("description"),
                        "url": source_data.get("url"),
                        "category": source_data.get("category"),
                        "language": source_data.get("language"),
                        "country_code": source_data.get("country"),
                        "country": db_country,
                    }

                    try:
                        source_obj, created = Source.objects.update_or_create(
                            api_id=api_id, defaults=defaults
                        )
                        if created:
                            total_sources_added += 1
                        else:
                            total_sources_processed_existing += 1

                    except IntegrityError as e:
                        logger.error(f"IntegrityError for source api_id {api_id}: {e}")
                    except Exception as e:
                        logger.error(
                            f"Could not save or update source {api_id} ('{source_data.get('name', '')}'): {e}"
                        )

            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed for country {db_country.code}: {e}")
                if "response" in locals() and response is not None:
                    logger.error(f"Failed URL: {response.url}")
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred while fetching sources for {db_country.code}: {e}"
                )

        logger.success(
            f"Finished populating sources. Added: {total_sources_added}, Processed existing (updated or unchanged): "
            f"{total_sources_processed_existing}"
        )
