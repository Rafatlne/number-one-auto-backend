import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
import re
from rest_framework.test import APIClient

User = get_user_model()

# Apply django_db mark at module level
pytestmark = pytest.mark.django_db

@pytest.fixture
def registration_url():
    return reverse('auth-register')

@pytest.fixture
def login_url():
    return reverse('auth-login')

@pytest.fixture
def additional_user_data():
    return {
        'username': 'existinguser',
        'email': 'existing@example.com',
        'password': 'securepassword123'
    }

@pytest.fixture
def existing_user(additional_user_data):
    return User.objects.create_user(**additional_user_data)

class TestRegistration:
    def test_register_with_username_only(self, api_client, registration_url):
        """Test user can register with just username and password"""
        data = {
            'username_email': 'usernameonly',
            'password': 'securepw123',
        }
        response = api_client.post(registration_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'token' in response.data
        assert 'user_id' in response.data
        assert User.objects.filter(username='usernameonly').exists()

    def test_register_with_email_only(self, api_client, registration_url):
        """Test user can register with just email and password"""
        data = {
            'username_email': 'valid@example.com',
            'password': 'securepw123',
        }
        response = api_client.post(registration_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'token' in response.data
        assert 'user_id' in response.data
        # Email should be converted to a username automatically
        assert User.objects.filter(email='valid@example.com').exists()
        
    def test_register_with_invalid_email(self, api_client, registration_url):
        """Test registration fails with invalid email format"""
        data = {
            'username_email': 'not-an-email',
            'password': 'securepw123',
        }
        response = api_client.post(registration_url, data, format='json')
        # This should still work as it would be treated as a username
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='not-an-email').exists()
        
    def test_register_with_invalid_email_format(self, api_client, registration_url):
        """Test registration fails with invalid email format that looks like an email"""
        data = {
            'username_email': 'invalid@email',  # Looks like email but invalid format
            'password': 'securepw123',
        }
        response = api_client.post(registration_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not User.objects.filter(username='invalid@email').exists()

    def test_register_with_existing_email(self, api_client, registration_url, existing_user):
        """Test registration fails with email that's already in use"""
        data = {
            'username_email': existing_user.email,  # Using existing email
            'password': 'securepw123',
        }
        response = api_client.post(registration_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data or 'username_email' in response.data

    def test_register_with_existing_username(self, api_client, registration_url, existing_user):
        """Test registration fails with username that's already in use"""
        data = {
            'username_email': existing_user.username,  # Using existing username
            'password': 'securepw123',
        }
        response = api_client.post(registration_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data or 'username_email' in response.data

    def test_register_missing_password(self, api_client, registration_url):
        """Test registration fails when password is missing"""
        data = {
            'username_email': 'newuser',
        }
        response = api_client.post(registration_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
        assert not User.objects.filter(username='newuser').exists()

class TestLogin:
    def test_login_with_username(self, api_client, login_url, existing_user, additional_user_data):
        """Test user can login with username"""
        data = {
            'identifier': additional_user_data['username'],
            'password': additional_user_data['password']
        }
        response = api_client.post(login_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data
        assert 'user_id' in response.data

    def test_login_with_email(self, api_client, login_url, existing_user, additional_user_data):
        """Test user can login with email"""
        data = {
            'identifier': additional_user_data['email'],
            'password': additional_user_data['password']
        }
        response = api_client.post(login_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data
        assert 'user_id' in response.data

    def test_login_with_invalid_email_format(self, api_client, login_url):
        """Test login fails with invalid email format"""
        data = {
            'identifier': 'not-an-email',
            'password': 'anypassword'
        }
        response = api_client.post(login_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_with_nonexistent_user(self, api_client, login_url):
        """Test login fails when user doesn't exist"""
        data = {
            'identifier': 'nonexistent@example.com',
            'password': 'anypassword'
        }
        response = api_client.post(login_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_with_incorrect_password(self, api_client, login_url, existing_user):
        """Test login fails with incorrect password"""
        data = {
            'identifier': existing_user.username,
            'password': 'wrongpassword'
        }
        response = api_client.post(login_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_identifier(self, api_client, login_url):
        """Test login fails when identifier is missing"""
        data = {
            'password': 'anypassword'
        }
        response = api_client.post(login_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_password(self, api_client, login_url):
        """Test login fails when password is missing"""
        data = {
            'identifier': 'any@example.com'
        }
        response = api_client.post(login_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
