"""
URL Configuration for PDA Template API

Note: This file is kept for backwards compatibility, but viewsets
are now registered in the centralized apps.api.urls module using PDARouter.
"""
from django.urls import path, include
from ..routers import PDARouter

from .views import TemplateViewSet

router = PDARouter()
router.register(r'', TemplateViewSet, basename='template')

app_name = "pdaTemplateAPI"
urlpatterns = [
    path('', include(router.urls)),
]