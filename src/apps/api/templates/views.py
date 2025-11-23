import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ZoneTemplate
from .serializers import ZoneTemplateSerializer


class TemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for fetching Accounts.

    Provides endpoints to list and retrieve Accounts from the database.
    """
    queryset = ZoneTemplate.objects.all()
    serializer_class = ZoneTemplateSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned records by filtering against
        query parameters in the URL.
        """
        queryset = ZoneTemplate.objects.all()

        # Filter by record name
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset.order_by('name')


    @action(detail=False, methods=['get', 'post'], url_path='zones')
    def accounts(self, request):
        return Response('TODO')