from django.contrib.auth import get_user_model
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import PersonalizedFeedFilter, SourceFilter
from .models import Country, Source, UserPreference, Article, UserArticle
from .serializers import (
    UserSerializer,
    CountrySerializer,
    SourceSerializer,
    UserPreferenceSerializer,
    ArticleSerializer,
)

User = get_user_model()


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @action(methods=["get"], detail=False, permission_classes=[permissions.IsAdminUser])
    def admins(self, request: Request):
        return Response({"youdidit": True})

    @action(methods=["get"], detail=False)
    def current(self, request):
        return Response(
            {
                "username": request.user.username,
            }
        )


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [permissions.IsAuthenticated]


class SourceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Source.objects.select_related('country').all()
    serializer_class = SourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = SourceFilter
    ordering = ['name']


class UserPreferenceViewSet(viewsets.ModelViewSet):
    queryset = UserPreference.objects.all()
    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "put", "patch"]

    def get_queryset(self):
        return UserPreference.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def my_preferences(self, request):
        preference, created = UserPreference.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(preference)
        return Response(serializer.data)

    @action(detail=False, methods=["put", "patch"], url_path="update-my-preferences")
    def update_my_preferences(self, request):
        preference, created = UserPreference.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(preference, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ArticlePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = ArticlePagination
    queryset = Article.objects.select_related('source').all()

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="personalized-feed",
    )
    def personalized_feed(self, request):
        user = request.user
        user_articles = UserArticle.objects.filter(user=user).values_list('article_id', flat=True)
        articles = Article.objects.filter(
            id__in=user_articles
        ).select_related('source').order_by("-published_at")
        filterset = PersonalizedFeedFilter(request.GET, queryset=articles, request=request)
        if filterset.is_valid():
            articles = filterset.qs
        
        page = self.paginate_queryset(articles)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)
