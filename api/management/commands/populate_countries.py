from loguru import logger
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from api.models import Country


class Command(BaseCommand):
    help = ("Populates the Country model with a predefined list of hardcoded "
            "ISO codes and their names using loguru for logging.")

    COUNTRY_MAPPING = {
        "ae": "United Arab Emirates",
        "ar": "Argentina",
        "at": "Austria",
        "au": "Australia",
        "be": "Belgium",
        "bg": "Bulgaria",
        "br": "Brazil",
        "ca": "Canada",
        "ch": "Switzerland",
        "cn": "China",
        "co": "Colombia",
        "cu": "Cuba",
        "cz": "Czechia",
        "de": "Germany",
        "eg": "Egypt",
        "fr": "France",
        "gb": "United Kingdom",
        "gr": "Greece",
        "hk": "Hong Kong",
        "hu": "Hungary",
        "id": "Indonesia",
        "ie": "Ireland",
        "il": "Israel",
        "in": "India",
        "it": "Italy",
        "jp": "Japan",
        "kr": "South Korea",
        "lt": "Lithuania",
        "lv": "Latvia",
        "ma": "Morocco",
        "mx": "Mexico",
        "my": "Malaysia",
        "ng": "Nigeria",
        "nl": "Netherlands",
        "no": "Norway",
        "nz": "New Zealand",
        "ph": "Philippines",
        "pl": "Poland",
        "pt": "Portugal",
        "ro": "Romania",
        "rs": "Serbia",
        "ru": "Russia",
        "sa": "Saudi Arabia",
        "se": "Sweden",
        "sg": "Singapore",
        "si": "Slovenia",
        "sk": "Slovakia",
        "th": "Thailand",
        "tr": "Turkey",
        "tw": "Taiwan",
        "ua": "Ukraine",
        "us": "United States",
        "ve": "Venezuela",
        "za": "South Africa",
    }

    def handle(self, *args, **options):
        logger.success("Starting to populate countries from hardcoded list...")
        countries_added = 0
        countries_skipped = 0

        for code, name in self.COUNTRY_MAPPING.items():
            try:
                country_obj, created = Country.objects.get_or_create(
                    code=code.lower(), defaults={"name": name}
                )

                if created:
                    countries_added += 1
                else:
                    if country_obj.name != name:
                        old_name = country_obj.name
                        country_obj.name = name
                        country_obj.save()
                    else:
                        logger.warning(
                            f"Skipped (already exists): {country_obj.name} ({code.upper()})"
                        )
                    countries_skipped += 1

            except IntegrityError as e:
                logger.error(f"IntegrityError for code {code.upper()}: {e}.")
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred for code {code.upper()} ({name}): {e}"
                )

        logger.success(
            f"Finished populating countries. Added: {countries_added}, Skipped/Existing/Updated: {countries_skipped}"
        )
