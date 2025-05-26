from django.db.models import QuerySet, Q
from rest_framework import filters
from rest_framework.request import Request
import django_filters
from .models import Article, Source


class PrimaryKeyFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request: Request, queryset: QuerySet, view):
        ids = request.query_params.get("ids")
        if ids:
            ids = list(map(int, ids.split(",")))
            queryset = queryset.filter(id__in=ids)
        return queryset


class ArticleFilter(django_filters.FilterSet):
    
    source_name = django_filters.CharFilter(
        field_name='source_name',
        lookup_expr='icontains',
        label='Filter by source name'
    )
    
    published_at = django_filters.DateFilter(
        field_name='published_at__date',
        label='Filter by exact publication date'
    )


    class Meta:
        model = Article
        fields = {
            'published_at': ['exact'],
            'fetched_at': ['exact', 'gte', 'lte'],
            'source_name': ['exact', 'icontains'],
        }

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(title__icontains=value) | Q(summary__icontains=value)
            )
        return queryset


class PersonalizedFeedFilter(ArticleFilter):
    keywords = django_filters.CharFilter(
        method='filter_keywords',
        label='Filter by user preference keywords'
    )
    
    source_id = django_filters.CharFilter(
        method='filter_preferred_sources',
        label='Show only articles from preferred source ID'
    )

    def filter_keywords(self, queryset, name, value):
        if value:
            keywords = [k.strip() for k in value.split(',')]
            q_objects = Q()
            for keyword in keywords:
                q_objects |= Q(title__icontains=keyword) | Q(summary__icontains=keyword)
            return queryset.filter(q_objects)
        return queryset

    def filter_preferred_sources(self, queryset, name, value):
        if value and value.isdigit():
            source_id = int(value)
            return queryset.filter(source_id=source_id)
        return queryset


class SourceFilter(django_filters.FilterSet):
    country_id = django_filters.CharFilter(
        method='filter_by_country_ids',
        label='Filter sources by country IDs (comma-separated)'
    )

    class Meta:
        model = Source
        fields = []

    def filter_by_country_ids(self, queryset, name, value):
        if value:
            country_ids = [int(id.strip()) for id in value.split(',') if id.strip().isdigit()]
            if country_ids:
                return queryset.filter(country__id__in=country_ids)
        return queryset
