import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from datetime import timedelta
from django.utils import timezone

from api.models import Country, Source, UserPreference, Article, UserArticle

User = get_user_model()


@pytest.mark.django_db
class TestUserViewSet:
    
    def test_list_users_authenticated(self, api_client, user_token):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('user-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
    
    def test_list_users_unauthenticated(self, api_client):
        url = reverse('user-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_retrieve_user(self, api_client, user, user_token):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('user-detail', kwargs={'pk': user.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'
    
    def test_current_user(self, api_client, user, user_token):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('user-current')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'
    
    def test_admins_endpoint_as_admin(self, api_client, admin_token):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {admin_token.key}')
        url = reverse('user-admins')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['youdidit'] is True
    
    def test_admins_endpoint_as_regular_user(self, api_client, user_token):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('user-admins')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCountryViewSet:
    
    def test_list_countries_authenticated(self, api_client, user_token, country):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('country-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'New Zealand'
    
    def test_list_countries_unauthenticated(self, api_client, country):
        url = reverse('country-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_retrieve_country(self, api_client, user_token, country):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('country-detail', kwargs={'pk': country.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == 'nz'


@pytest.mark.django_db
class TestSourceViewSet:
    
    def test_sources_filter_by_multiple_country_ids(self, api_client, user_token):
        country1 = Country.objects.create(name="New Zealand", code="nz")
        country2 = Country.objects.create(name="United States", code="us")
        country3 = Country.objects.create(name="United Kingdom", code="gb")
        
        source1 = Source.objects.create(api_id="nz-herald", name="NZ Herald", country=country1)
        source2 = Source.objects.create(api_id="cnn", name="CNN", country=country2)
        source3 = Source.objects.create(api_id="bbc-news", name="BBC News", country=country3)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('source-list')
        country_ids = f"{country1.id},{country2.id}"
        response = api_client.get(url, {'country_id': country_ids})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        source_names = [source['name'] for source in response.data]
        assert 'NZ Herald' in source_names
        assert 'CNN' in source_names
        assert 'BBC News' not in source_names
    
    def test_sources_filter_by_country_ids_with_spaces(self, api_client, user_token):
        country1 = Country.objects.create(name="New Zealand", code="nz")
        country2 = Country.objects.create(name="United States", code="us")
        
        source1 = Source.objects.create(api_id="nz-herald", name="NZ Herald", country=country1)
        source2 = Source.objects.create(api_id="cnn", name="CNN", country=country2)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('source-list')
        country_ids = f" {country1.id} , {country2.id} "
        response = api_client.get(url, {'country_id': country_ids})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    
    def test_sources_without_country_id_filter_returns_all(self, api_client, user_token):
        country1 = Country.objects.create(name="New Zealand", code="nz")
        country2 = Country.objects.create(name="United States", code="us")
        
        source1 = Source.objects.create(api_id="nz-herald", name="NZ Herald", country=country1)
        source2 = Source.objects.create(api_id="cnn", name="CNN", country=country2)
        source3 = Source.objects.create(api_id="reuters", name="Reuters", country=None)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('source-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3


@pytest.mark.django_db
class TestUserPreferenceViewSet:
    
    def test_get_queryset_filters_by_user(self, api_client, user, user_token):
        other_user = User.objects.create_user(username='other', password='pass')
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('userpreference-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        for pref in response.data:
            assert pref['user'] == user.pk
    
    def test_my_preferences_get(self, api_client, user, user_token):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('userpreference-my-preferences')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user'] == user.pk

    
    def test_update_my_preferences_put(self, api_client, user, user_token, country, source):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('userpreference-update-my-preferences')
        data = {
            'keywords': ['technology', 'science'],
            'preferred_country_codes': [country.id],
            'preferred_source_api_ids': [source.id]
        }
        response = api_client.put(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        preference = UserPreference.objects.get(user=user)
        assert preference.keywords == ['technology', 'science']
    
    def test_update_my_preferences_patch(self, api_client, user, user_token):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('userpreference-update-my-preferences')
        data = {'keywords': ['updated']}
        response = api_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
    
    def test_unauthenticated_access_denied(self, api_client):
        url = reverse('userpreference-my-preferences')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestArticleViewSet:
    
    def test_list_articles_authenticated(self, api_client, user_token, articles):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('article-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
    
    def test_list_articles_unauthenticated(self, api_client, articles):
        url = reverse('article-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_retrieve_article(self, api_client, user_token, article):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('article-detail', kwargs={'pk': article.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Test Article'
    
    def test_article_pagination(self, api_client, user_token):
        for i in range(25):
            Article.objects.create(
                title=f'Article {i}',
                article_url=f'https://example.com/article-{i}',
                published_at=timezone.now() - timedelta(hours=i)
            )
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('article-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 20
        assert response.data['next'] is not None
    
    def test_article_search(self, api_client, user_token, articles):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('article-list')
        response = api_client.get(url, {'keywords': 'Article 1'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
    
    def test_article_filter_by_source_id(self, api_client, user_token, articles, source):
        Article.objects.create(
            title='Different Source Article',
            article_url='https://example.com/different',
            published_at=timezone.now()
        )
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('article-list')
        response = api_client.get(url, {'source_id': source.id})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 6
    
    def test_article_ordering(self, api_client, user_token, articles):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('article-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['title'] == 'Article 0'
    
    def test_personalized_feed_no_preferences(self, api_client, user, user_token, articles):
        UserPreference.objects.filter(user=user).delete()
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('article-personalized-feed')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
    
    def test_personalized_feed_with_user_articles(self, api_client, user, user_token, articles):
        UserArticle.objects.create(user=user, article=articles[0])
        UserArticle.objects.create(user=user, article=articles[1])
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('article-personalized-feed')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        article_ids = [article['id'] for article in response.data['results']]
        assert articles[0].id in article_ids
        assert articles[1].id in article_ids
    
    def test_personalized_feed_pagination(self, api_client, user, user_token):
        articles = []
        for i in range(25):
            article = Article.objects.create(
                title=f'Personal Article {i}',
                article_url=f'https://example.com/personal-{i}',
                published_at=timezone.now() - timedelta(hours=i)
            )
            articles.append(article)
            UserArticle.objects.create(user=user, article=article)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('article-personalized-feed')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 20
        assert response.data['next'] is not None
    
    def test_personalized_feed_unauthenticated(self, api_client):
        url = reverse('article-personalized-feed')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_article_readonly_methods_only(self, api_client, user_token, article):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        
        url = reverse('article-list')
        data = {
            'title': 'New Article',
            'article_url': 'https://example.com/new',
            'published_at': timezone.now()
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        url = reverse('article-detail', kwargs={'pk': article.pk})
        response = api_client.put(url, data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_article_filter_date_range(self, api_client, user_token):
        now = timezone.now()
        Article.objects.create(
            title='Recent Article',
            article_url='https://example.com/recent',
            published_at=now
        )
        Article.objects.create(
            title='Old Article',
            article_url='https://example.com/old',
            published_at=now - timedelta(days=7)
        )

        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('article-list')

        response = api_client.get(url, {
            'published_at': now.isoformat()
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert response.data['results'][0]['title'] == 'Recent Article'
        assert response.data['results'][1]['title'] == 'Old Article'


@pytest.mark.django_db
class TestArticlePagination:
    
    def test_custom_page_size(self, api_client, user_token):
        for i in range(30):
            Article.objects.create(
                title=f'Article {i}',
                article_url=f'https://example.com/article-{i}',
                published_at=timezone.now() - timedelta(hours=i)
            )
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('article-list')
        
        response = api_client.get(url, {'page_size': 10})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 10
        
        response = api_client.get(url, {'page_size': 150})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 30


@pytest.mark.django_db
class TestViewSetIntegration:
    
    def test_full_user_workflow(self, api_client, user, user_token, country, source):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        
        response = api_client.get(reverse('user-current'))
        assert response.status_code == status.HTTP_200_OK
        
        response = api_client.get(reverse('userpreference-my-preferences'))
        assert response.status_code == status.HTTP_200_OK
        
        data = {'keywords': ['updated', 'keywords']}
        response = api_client.patch(
            reverse('userpreference-update-my-preferences'),
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        
        response = api_client.get(reverse('article-personalized-feed'))
        assert response.status_code == status.HTTP_200_OK
    
    def test_preferences_with_relationships(self, api_client, user, user_token, country, source):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        
        preference = UserPreference.objects.get(user=user)
        preference.preferred_countries.add(country)
        preference.preferred_sources.add(source)
        preference.keywords = ['technology', 'science']
        preference.save()
        
        response = api_client.get(reverse('userpreference-my-preferences'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['preferred_countries']) == 1
        assert len(response.data['preferred_sources']) == 1
        assert response.data['keywords'] == ['technology', 'science']
        assert response.data['preferred_countries'][0]['code'] == 'nz'
        assert response.data['preferred_sources'][0]['api_id'] == 'bbc-news'


@pytest.mark.django_db
class TestErrorHandling:
    
    def test_invalid_token(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION='Token invalid-token')
        url = reverse('user-current')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_missing_token(self, api_client):
        url = reverse('user-current')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_nonexistent_article(self, api_client, user_token):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('article-detail', kwargs={'pk': 99999})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_nonexistent_country(self, api_client, user_token):
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        url = reverse('country-detail', kwargs={'pk': 99999})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
