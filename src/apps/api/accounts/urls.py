"""
URL Configuration for PDA Account API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AccountViewSet

router = DefaultRouter()
router.register(r'', AccountViewSet, basename='record')

app_name = "pdaAccountApi"
urlpatterns = [
    path('', include(router.urls)),
]