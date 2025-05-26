from django.urls import include, path
from rest_framework import routers

from . import views
from .auth import AuthViewSet

router = routers.DefaultRouter()
router.register(r"auth", AuthViewSet, basename="auth")
router.register(r"users", views.UserViewSet, basename="user")
router.register(r"countries", views.CountryViewSet, basename="country")
router.register(r"sources", views.SourceViewSet, basename="source")
router.register(r"user-preferences", views.UserPreferenceViewSet, basename="userpreference")
router.register(r"articles", views.ArticleViewSet, basename="article")

urlpatterns = [
    path("", include(router.urls)),
]
