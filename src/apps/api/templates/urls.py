"""
URL Configuration for PowerDNS API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TemplateViewSet

router = DefaultRouter()
router.register(r'', TemplateViewSet, basename='record')

app_name = "pdaTemplateAPI"
urlpatterns = [
    path('', include(router.urls)),
]