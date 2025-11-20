"""
URL Configuration for PowerDNS API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RecordViewSet
from . import views

router = DefaultRouter()
router.register(r'records', RecordViewSet, basename='record')

app_name = "pdadns"
urlpatterns = [
    path("", views.domains, name="domains"),
    path('', include(router.urls)),
    path("domain/<str:id>/", views.domain, name="domain"),
]

