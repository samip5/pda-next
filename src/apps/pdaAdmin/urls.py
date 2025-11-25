from django.urls import path

from . import views

app_name = "pdaAdmin"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("settings/", views.settings, name="settings"),
    path("accounts/", views.accounts, name="accounts"),
    path("accounts/<str:id>/", views.account, name="account"),
    path("zones/", views.zones, name="zones"),
    path("zones/<str:id>/", views.zone, name="zone"),
    path("zones/<str:id>/delete", views.delete_zone_view, name="delete_zone"),
    path("templates/", views.templates, name="templates"),
    path("templates/<str:id>/", views.edit_template, name="edit_template"),
    path("clear_cache", views.clear_cache, name="clear_cache"),
    path('users/', views.users, name="users"),
    path('users/<str:id>', views.user, name="user"),

]
