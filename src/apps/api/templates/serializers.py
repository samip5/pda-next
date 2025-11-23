"""
Serializers for PowerDNS API
"""
from rest_framework import serializers

from apps.api.templates.models import RecordTemplate, ZoneTemplate


class RecordTemplateSerializer(serializers.ModelSerializer):
    """Serializer for DNS Record model"""

    class Meta:
        model = RecordTemplate
        fields = [
            'zone_template',
            'name',
            'record_type',
            'content',
            'ttl',
        ]
        read_only_fields = ['id']

class ZoneTemplateSerializer(serializers.ModelSerializer):
    """Serializer for DNS Zone model"""

    class Meta:
        model = ZoneTemplate
        fields = [
            'id',
            'name',
            'kind',
            'account',
            'nameservers'
        ]
        read_only_fields = ['id']

