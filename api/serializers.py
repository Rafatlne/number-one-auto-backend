from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import UserPreference, Article, UserArticle, Source, Country
from rest_framework.authtoken.models import Token

User = get_user_model()


class EmailAuthTokenSerializer(serializers.Serializer):
    username_email = serializers.CharField(label="Username or Email", write_only=True)
    password = serializers.CharField(
        label="Password",
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(label="Token", read_only=True)

    def validate(self, attrs):
        username_email = attrs.get('username_email')
        password = attrs.get('password')

        if username_email and password:
            import re
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            is_email_format = bool(email_pattern.match(username_email))

            if is_email_format:
                from django.core.validators import validate_email
                from django.core.exceptions import ValidationError
                try:
                    validate_email(username_email)
                except ValidationError:
                    msg = 'Please enter a valid email address.'
                    raise serializers.ValidationError(msg, code='invalid_email')

                try:
                    user_by_email = User.objects.get(email=username_email)
                    user = authenticate(request=self.context.get('request'),
                                        username=user_by_email.username,
                                        password=password)
                except User.DoesNotExist:
                    user = authenticate(request=self.context.get('request'),
                                        username=username_email,
                                        password=password)
            else:
                user = authenticate(request=self.context.get('request'),
                                    username=username_email,
                                    password=password)

            if not user:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include both username/email and password.'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
        'id', 'username', 'email', 'first_name', 'last_name', 'bio', 'profile_picture', 'date_of_birth', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'name', 'code')


class SourceSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    country_code = serializers.CharField(source='country.code', read_only=True)

    class Meta:
        model = Source
        fields = ('id', 'name', 'api_id', 'description', 'url', 'category',
                  'language', 'country_code', 'country_name')


class UserPreferenceSerializer(serializers.ModelSerializer):
    preferred_countries = CountrySerializer(many=True, read_only=True)
    preferred_sources = SourceSerializer(many=True, read_only=True)
    preferred_country_codes = serializers.ListField(
        child=serializers.CharField(max_length=2), write_only=True, required=False
    )
    preferred_source_api_ids = serializers.ListField(
        child=serializers.CharField(max_length=100), write_only=True, required=False
    )

    class Meta:
        model = UserPreference
        fields = (
            'id',
            'user',
            'preferred_countries',
            'preferred_sources',
            'keywords',
            'created_at',
            'updated_at',
            'preferred_country_codes',
            'preferred_source_api_ids'
        )
        read_only_fields = ('user', 'created_at', 'updated_at', 'preferred_countries', 'preferred_sources')

    def update(self, instance, validated_data):
        if 'preferred_country_codes' in validated_data:
            country_codes = validated_data.pop('preferred_country_codes')
            instance.preferred_countries.set(Country.objects.filter(id__in=country_codes))

        if 'preferred_source_api_ids' in validated_data:
            source_api_ids = validated_data.pop('preferred_source_api_ids')
            instance.preferred_sources.set(Source.objects.filter(id__in=source_api_ids))

        instance.keywords = validated_data.get('keywords', instance.keywords)
        instance.save()
        return instance


class ArticleSerializer(serializers.ModelSerializer):
    source = SourceSerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'summary',
            'article_url',
            'source_name',
            'source',
            'image_url',
            'published_at',
            'fetched_at'
        ]


class UserRegistrationWithEmailSerializer(serializers.Serializer):
    username_email = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_username_email(self, value):
        import re

        if '@' in value:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise serializers.ValidationError("Enter a valid email address.")

            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        else:
            if User.objects.filter(username=value).exists():
                raise serializers.ValidationError("A user with this username already exists.")

        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def create(self, validated_data):
        from .services import AuthService

        username_email = validated_data['username_email']
        password = validated_data['password']
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')

        user, token = AuthService.create_user_with_preferences(
            username_email, password, first_name, last_name
        )

        user.token = token
        return user


class UserArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserArticle
        fields = ['id', 'user', 'article']
        read_only_fields = ['id']
