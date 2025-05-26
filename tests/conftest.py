import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from datetime import timedelta
from django.utils import timezone

from api.models import Country, Source, Article, UserPreference, UserArticle

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def user_token(user):
    token, created = Token.objects.get_or_create(user=user)
    return token


@pytest.fixture
def admin_token(admin_user):
    token, created = Token.objects.get_or_create(user=admin_user)
    return token


@pytest.fixture
def country():
    return Country.objects.create(name='New Zealand', code='nz')


@pytest.fixture
def source():
    return Source.objects.create(api_id='bbc-news', name='BBC News')


@pytest.fixture
def article():
    return Article.objects.create(
        title='Test Article',
        summary='Test Summary',
        source_name='BBC News',
        article_url='https://example.com/test',
        published_at=timezone.now()
    )


@pytest.fixture
def articles():
    articles = []
    for i in range(5):
        article = Article.objects.create(
            title=f'Article {i}',
            summary=f'Summary {i}',
            source_name='Test Source',
            article_url=f'https://example.com/article-{i}',
            published_at=timezone.now() - timedelta(hours=i)
        )
        articles.append(article)
    return articles

