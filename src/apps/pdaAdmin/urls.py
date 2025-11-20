from django.urls import path

from . import views

app_name = "pdaAdmin"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("settings/", views.settings, name="settings")
]
