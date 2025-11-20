"""
URL Configuration for PowerDNS API
"""
from django.urls import path
from . import views

app_name = "pdadns"
urlpatterns = [
    path("", views.domains, name="domains"),
    path("domain/<str:id>/", views.domain, name="domain"),
]

