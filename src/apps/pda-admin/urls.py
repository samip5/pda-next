from django.urls import path

from . import views

app_name = "pda-admin"
urlpatterns = [
    path("", views.profile, name="dashboard"),
    path("settings/", views.settings, name="settings")
]
