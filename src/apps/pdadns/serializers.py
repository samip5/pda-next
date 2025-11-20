"""
Serializers for PowerDNS API
"""
from rest_framework import serializers
from .models.record import Record
from .models.zone import Zone


class RecordSerializer(serializers.ModelSerializer):
    """Serializer for DNS Record model"""
    
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    fqdn = serializers.SerializerMethodField()
    
    class Meta:
        model = Record
        fields = [
            'id',
            'zone',
            'zone_name',
            'name',
            'fqdn',
            'record_type',
            'content',
            'ttl',
            'disabled',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_fqdn(self, obj):
        """Get fully qualified domain name"""
        return obj.get_fqdn()


class ZoneSerializer(serializers.ModelSerializer):
    """Serializer for DNS Zone model"""
    
    class Meta:
        model = Zone
        fields = [
            'id',
            'name',
            'kind',
            'nameservers',
            'server_id',
            'powerdns_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'powerdns_id']

