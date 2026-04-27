from rest_framework import serializers
from .models import Table, CustomerSession


class TableSerializer(serializers.ModelSerializer):
    active_sessions = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = ['id', 'number', 'is_open', 'is_active', 'created_at', 'active_sessions']

    def get_active_sessions(self, obj):
        return obj.sessions.filter(is_active=True).count()


# class BulkTableSerializer(serializers.Serializer):
#     numbers = serializers.ListField(
#         child=serializers.IntegerField(min_value=1),
#         allow_empty=False
#     )

class BulkTableSerializer(serializers.Serializer):
    numbers = serializers.ListField(
        child=serializers.CharField(max_length=20),
        allow_empty=False
    )


class CustomerSessionSerializer(serializers.ModelSerializer):
    table_number = serializers.CharField(source='table.number', read_only=True)

    class Meta:
        model = CustomerSession
        fields = ['id', 'customer_name', 'table', 'table_number', 'session_token', 'expires_at', 'is_active']
        read_only_fields = ['session_token', 'expires_at', 'is_active']


class ScanQRSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    customer_name = serializers.CharField(max_length=100)