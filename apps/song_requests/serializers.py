from rest_framework import serializers
from .models import SongRequest


class SongRequestSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='session.customer_name', read_only=True)
    table_number = serializers.IntegerField(source='session.table.number', read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = SongRequest
        fields = [
            'id', 'song_title', 'artist', 'donation_amount',
            'status', 'status_display', 'customer_name', 'table_number',
            'admin_reviewed_at', 'dj_reviewed_at', 'created_at',
        ]
        read_only_fields = ['status', 'admin_reviewed_at', 'dj_reviewed_at', 'created_at']

    def get_status_display(self, obj):
        return obj.get_status_display_id()


class SongRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SongRequest
        fields = ['song_title', 'artist', 'donation_amount']

    def validate_donation_amount(self, value):
        if value < 10000:
            raise serializers.ValidationError('Minimum donation is Rp 10.000')
        return value

    # def validate(self, data):
    #     session = self.context.get('session')
    #     count = SongRequest.objects.filter(
    #         session=session,
    #         status__in=[
    #             SongRequest.STATUS_PENDING,
    #             SongRequest.STATUS_ADMIN_APPROVED,
    #             SongRequest.STATUS_DJ_APPROVED,
    #         ]
    #     ).count()
    #     if count >= 5:
    #         raise serializers.ValidationError(
    #             'Maximum 5 song requests per session'
    #         )
    #     return data