"""
Serializers for PDA Account API
"""
from rest_framework import serializers
from .models.account import Account


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for Account model"""

    class Meta:
        model = Account
        fields = [
            'id',
            'name',
            'description',
            'contact',
            'mail'
        ]
        read_only_fields = ['id']

    def get_fqdn(self, obj):
        """Get fully qualified domain name"""
        return obj.get_fqdn()

