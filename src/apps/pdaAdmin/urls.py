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

]
