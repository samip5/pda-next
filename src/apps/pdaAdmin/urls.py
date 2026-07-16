from django.urls import path

from . import views

app_name = "pdaAdmin"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("settings/", views.settings, name="settings"),
    path("accounts/", views.accounts, name="accounts"),
    path("accounts/<str:id>/", views.account, name="account"),
    path("accounts/<str:id>/delete", views.delete_account_view, name="delete_account"),
    path("zones/", views.zones, name="zones"),
    path("zones/<str:id>/", views.zone, name="zone"),
    path("zones/<str:id>/delete", views.delete_zone_view, name="delete_zone"),
    path("templates/", views.templates, name="templates"),
    path("templates/<str:id>/", views.edit_template, name="edit_template"),
    path("templates/<str:id>/delete", views.delete_template_view, name="delete_template"),
    path("clear_cache", views.clear_cache, name="clear_cache"),
    path('users/', views.users, name="users"),
    path('users/<str:id>', views.user, name="user"),
    path("users/<str:id>/delete", views.delete_user_view, name="delete_user"),
    path('groups/', views.groups, name="groups"),
    path('groups/<str:id>', views.group, name="group"),
    path("groups/<str:id>/delete", views.delete_group_view, name="delete_group"),

]
