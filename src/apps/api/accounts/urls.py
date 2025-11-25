"""
URL Configuration for PDA Account API

Note: This file is kept for backwards compatibility, but viewsets
are now registered in the centralized apps.api.urls module using PDARouter.
"""
from django.urls import path, include
from ..routers import PDARouter

from .views import AccountViewSet

router = PDARouter()
router.register(r'', AccountViewSet, basename='account')

app_name = "pdaAccountApi"
urlpatterns = [
    path('', include(router.urls)),
]