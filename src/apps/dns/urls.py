from django.urls import path

from . import views

app_name = "dns"
urlpatterns = [
    path("", views.domains, name="domains"),
    path("domain/<str:id>/", views.domain, name="domain"),
]
