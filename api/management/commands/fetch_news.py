from collections import defaultdict
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from loguru import logger

from api.models import UserPreference, Article, UserArticle, Source, Country

NEWSAPI_BASE_URL = "https://newsapi.org/v2/everything"
MAX_QUERY_LENGTH = 500
MAX_SOURCES = 20

User = get_user_model()


class Command(BaseCommand):
    help = "Fetches news articles from NewsAPI /v2/everything endpoint with keyword batching"

    def __init__(self):
        super().__init__()
        logger.add("logs/fetch_news.log", rotation="1 day", retention="30 days")

    def handle(self, *args, **options):
        logger.info("Starting news fetch command")

        user_prefs = self.get_user_preferences()
        if not user_prefs:
            logger.warning("No user preferences found")
            return

        country_data = self.organize_by_country(user_prefs)

        all_articles_dict = {}
        for country_code, data in country_data.items():
            articles = self.fetch_articles_for_country(country_code, data)
            for article in articles:
                url = article.get("url")
                if url and url not in all_articles_dict:
                    all_articles_dict[url] = article

        all_articles = list(all_articles_dict.values())
        logger.info(f"Total unique articles: {len(all_articles)}")

        if all_articles:
            self.process_and_link_articles(all_articles, user_prefs)

        logger.info(
            f"News fetch completed. Total articles processed: {len(all_articles)}"
        )

    def get_user_preferences(self):
        preferences = (
            UserPreference.objects.select_related("user")
            .prefetch_related("preferred_countries", "preferred_sources")
            .all()
        )

        logger.info(f"Found {preferences.count()} user preferences")
        return list(preferences)

    def organize_by_country(self, user_prefs):
        country_data = defaultdict(
            lambda: {"users": set(), "sources": set(), "all_keywords": []}
        )

        for pref in user_prefs:
            countries = list(pref.preferred_countries.all())
            if not countries:
                logger.warning(f"No countries found for user {pref.user.username}")
                continue

            for country in countries:
                country_code = country.code.lower()
                country_data[country_code]["users"].add(pref.user.id)
                country_data[country_code]["all_keywords"].extend(pref.keywords)

                for source in pref.preferred_sources.all():
                    if source.country.id == country.id:
                        country_data[country_code]["sources"].add(source.api_id)

        final_country_data = {}
        for country_code, data in country_data.items():
            if not data["sources"]:
                logger.warning(f"Skipping country {country_code} - no sources")
                continue

            keyword_batches = self.create_keyword_batches(data["all_keywords"])
            if not keyword_batches:
                logger.warning(f"Skipping country {country_code} - no keywords")
                continue

            final_country_data[country_code] = {
                "users": list(data["users"]),
                "sources": list(data["sources"])[:MAX_SOURCES],
                "keyword_batches": keyword_batches,
            }

            logger.info(
                f"Country {country_code}: {len(data['users'])} users, "
                f"{len(data['sources'])} sources, {len(keyword_batches)} keyword batches"
            )

        return final_country_data

    def create_keyword_batches(self, all_keywords):
        if not all_keywords:
            return []

        unique_keywords = set(
            keyword.lower().strip() for keyword in all_keywords if keyword.strip()
        )
        if not unique_keywords:
            return []

        keywords_list = list(unique_keywords)
        logger.info(f"Processing {len(keywords_list)} unique keywords")
        batches = []
        current_batch = []
        current_length = 0

        for keyword in keywords_list:
            keyword_with_quotes = f'"{keyword}"'
            space_needed = len(keyword_with_quotes)
            if current_batch:
                space_needed += len(" OR ")

            if not current_batch and space_needed > MAX_QUERY_LENGTH:
                logger.warning(f"Keyword too long, skipping: {keyword}")
                continue

            if current_batch and current_length + space_needed > MAX_QUERY_LENGTH:
                batches.append(current_batch)
                current_batch = []
                current_length = 0

            if current_batch:
                current_length += len(" OR ")
            current_batch.append(keyword)
            current_length += len(keyword_with_quotes)

        if current_batch:
            batches.append(current_batch)

        logger.info(f"Created {len(batches)} keyword batches")
        return batches

    def fetch_articles_for_country(self, country_code, country_data):
        logger.info(f"Fetching articles for country: {country_code}")

        if not settings.NEWSAPI_KEY:
            logger.error("NEWSAPI_KEY not configured")
            return []

        sources = country_data["sources"]
        keyword_batches = country_data["keyword_batches"]

        to_time = datetime.now()
        from_time = to_time - timedelta(hours=24)
        to_time_str = to_time.strftime("%Y-%m-%d")
        from_time_str = from_time.strftime("%Y-%m-%d")

        country_articles = {}
        sources_string = ",".join(sources)

        for batch_idx, keywords in enumerate(keyword_batches):
            raw_query = " OR ".join(f'"{keyword}"' for keyword in keywords)

            params = {
                "apiKey": settings.NEWSAPI_KEY,
                "q": raw_query,
                "searchIn": "title,content",
                "to": to_time_str,
                "from": from_time_str,
                "pageSize": 100,
                "sortBy": "publishedAt",
                "sources": sources_string,
            }

            try:
                response = requests.get(NEWSAPI_BASE_URL, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                if data.get("status") == "error":
                    logger.error(f"NewsAPI error: {data.get('message')}")
                    continue

                articles = data.get("articles", [])

                for article in articles:
                    url = article.get("url")
                    if url and url not in country_articles:
                        country_articles[url] = article

            except Exception as e:
                logger.error(
                    f"API request failed for {country_code}, batch {batch_idx}: {e}"
                )
                continue

        logger.info(
            f"Country {country_code}: collected {len(country_articles)} articles"
        )
        return list(country_articles.values())

    def process_and_link_articles(self, articles_data, user_prefs):
        logger.info(
            f"Processing {len(articles_data)} articles for {len(user_prefs)} users"
        )

        users_by_source = defaultdict(set)
        users_by_keyword = defaultdict(set)
        users_with_no_sources = set()
        users_with_no_keywords = set()

        for pref in user_prefs:
            user_id = pref.user.id
            sources = {source.api_id for source in pref.preferred_sources.all()}
            if sources:
                for source_id in sources:
                    users_by_source[source_id].add(user_id)
            else:
                users_with_no_sources.add(user_id)

            keywords = [kw.lower().strip() for kw in pref.keywords or [] if kw and kw.strip()]
            if keywords:
                for keyword in keywords:
                    users_by_keyword[keyword].add(user_id)
            else:
                users_with_no_keywords.add(user_id)

        new_articles = 0
        user_articles_to_create = []

        for article_data in articles_data:
            url = article_data.get("url")
            title = article_data.get("title")
            published_at_str = article_data.get("publishedAt")
            source_info = article_data.get("source", {})
            source_id = source_info.get("id")
            source_name = source_info.get("name")
            description = article_data.get("description")
            image_url = article_data.get("urlToImage")

            # Skip articles missing essential information
            if not url or not title or not published_at_str:
                continue

            # Parse published date
            try:
                published_at = parse_datetime(published_at_str)
                if not published_at:
                    continue
            except (ValueError, TypeError):
                continue

            try:
                source_obj = Source.objects.get(api_id=source_id)
            except Source.DoesNotExist:
                source_obj = None

            article, created = Article.objects.get_or_create(
                article_url=url,
                defaults={
                    "title": title,
                    "summary": description,
                    "source_name": source_name,
                    "source": source_obj,
                    "image_url": image_url,
                    "published_at": published_at,
                },
            )

            if created:
                new_articles += 1

            matching_users = self.find_matching_users_optimized(
                article,
                source_id,
                users_by_source,
                users_by_keyword,
                users_with_no_sources,
                users_with_no_keywords,
            )
            user_articles_to_create += [
                UserArticle(user_id=user_id, article=article) for user_id in matching_users
            ]

        if user_articles_to_create:
            UserArticle.objects.bulk_create(
                user_articles_to_create, ignore_conflicts=True
            )
        new_links = len(user_articles_to_create)

        logger.info(
            f"Processing complete: {new_articles} new articles, {new_links} new links"
        )

    def find_matching_users_optimized(
            self,
            article,
            source_id,
            users_by_source,
            users_by_keyword,
            users_with_no_sources,
            users_with_no_keywords,
    ):
        source_matching_users = set()
        if source_id and source_id in users_by_source:
            source_matching_users.update(users_by_source[source_id])
        source_matching_users.update(users_with_no_sources)

        keyword_matching_users = set()
        article_text = ""
        if article.title:
            article_text += article.title.lower() + " "
        if article.summary:
            article_text += article.summary.lower()

        for keyword, user_set in users_by_keyword.items():
            if keyword in article_text:
                keyword_matching_users.update(user_set)

        keyword_matching_users.update(users_with_no_keywords)

        return source_matching_users & keyword_matching_users
