from rest_framework.authtoken.models import Token
from .models import User, Country, Source, UserPreference
import re


class AuthService:
    
    @staticmethod
    def create_user_with_preferences(username_email, password, first_name='', last_name=''):
        is_email = AuthService._is_valid_email(username_email)
        
        if is_email:
            username = AuthService._generate_unique_username_from_email(username_email)
            user = User.objects.create_user(
                username=username,
                email=username_email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
        else:
            user = User.objects.create_user(
                username=username_email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
        
        token, _ = Token.objects.get_or_create(user=user)
        
        AuthService._setup_default_preferences(user)
        
        return user, token
    
    @staticmethod
    def _is_valid_email(email):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    @staticmethod
    def _generate_unique_username_from_email(email):
        username = email.split('@')[0]
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        return username
    
    @staticmethod
    def _setup_default_preferences(user):
        user_pref = UserPreference.objects.get(user=user)
        
        try:
            default_country_nz = Country.objects.get(code='nz')
            user_pref.preferred_countries.add(default_country_nz)
        except Country.DoesNotExist:
            pass
        
        try:
            default_sources = Source.objects.filter(api_id__in=['bbc-news', 'cnn'])
            user_pref.preferred_sources.add(*default_sources)
        except Source.DoesNotExist:
            pass
