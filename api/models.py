from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

DEFAULT_KEYWORDS = ["car", "automobile"]

def get_default_keywords():
    return list(DEFAULT_KEYWORDS)

class User(AbstractUser):
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.username


class Country(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Full name of the country (e.g., New Zealand).",
    )
    code = models.CharField(
        max_length=2, unique=True, help_text="Two-letter ISO country code (e.g., 'nz')."
    )

    def __str__(self):
        return f"{self.name} ({self.code.upper()})"

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name"]


class Source(models.Model):
    api_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="The identifier for the source from NewsAPI.org (e.g., 'bbc-news').",
    )
    name = models.CharField(
        max_length=150,
        help_text="The display name of the news source (e.g., BBC News).",
    )
    description = models.TextField(
        blank=True, null=True, help_text="A description of the source."
    )
    url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="The homepage URL of the source.",
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="The category of the source (e.g., technology, sports).",
    )
    language = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="The language of the source (e.g., en).",
    )
    country_code = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        help_text="The country this source is primarily from.",
    )
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="sources", null=True, blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class UserPreference(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="preferences"
    )

    preferred_countries = models.ManyToManyField(
        Country,
        blank=True,
        help_text="User's preferred countries for news.",
    )
    preferred_sources = models.ManyToManyField(
        Source,
        blank=True,
        help_text="User's preferred news sources.",
    )

    keywords = models.JSONField(
        default=get_default_keywords, help_text="List of preferred keywords."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"


class Article(models.Model):
    title = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    article_url = models.URLField(unique=True)
    source_name = models.CharField(max_length=100, blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    image_url = models.URLField(max_length=2000, blank=True, null=True)
    published_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title


class UserArticle(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="feed_articles"
    )
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="users_in_feed"
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "article")
        ordering = ["-article__published_at"]

    def __str__(self):
        return f"{self.user.username} - {self.article.title}"
