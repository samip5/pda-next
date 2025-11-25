import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import ZoneTemplate
from .serializers import ZoneTemplateSerializer


class TemplateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ZoneTemplate.objects.all()
    serializer_class = ZoneTemplateSerializer

    def get_queryset(self):
        queryset = ZoneTemplate.objects.all()

        # Filter by record name
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset.order_by('name')

    @extend_schema(
        summary="List all zone templates",
        description="Returns a paginated list of all zone templates. Results are paginated with 100 items per page.",
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Page number (default: 1)',
                required=False,
            ),
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter templates by name (case-insensitive partial match)',
                required=False,
            ),
        ],
        responses={
            200: ZoneTemplateSerializer,
        },
    )
    def list(self, request):
        return super().list(request)

    @extend_schema(
        summary="Retrieve a specific zone template",
        description="Returns details of a single zone template by ID.",
        responses={
            200: ZoneTemplateSerializer,
            404: OpenApiTypes.OBJECT,
        },
    )
    def retrieve(self, request, pk=None):
        return super().retrieve(request, pk)

    @extend_schema(
        methods=['GET'],
        summary="List template zones (TODO)",
        description="This endpoint is not yet implemented.",
        responses={
            200: OpenApiTypes.STR,
        },
    )
    @action(detail=False, methods=['get', 'post'], url_path='zones')
    def accounts(self, request):
        return Response('TODO')