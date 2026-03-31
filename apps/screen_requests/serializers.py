from rest_framework import serializers
from .models import ScreenRequest

# 10MB for photos, 50MB for videos
MAX_PHOTO_SIZE = 10 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024


class ScreenRequestSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='session.customer_name', read_only=True)
    table_number = serializers.IntegerField(source='session.table.number', read_only=True)

    class Meta:
        model = ScreenRequest
        fields = [
            'id', 'request_type', 'message', 'media_file',
            'donation_amount', 'status', 'customer_name',
            'table_number', 'reviewed_at', 'created_at',
        ]
        read_only_fields = ['status', 'reviewed_at', 'created_at']


class ScreenRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreenRequest
        fields = ['request_type', 'message', 'media_file', 'donation_amount']

    def validate_donation_amount(self, value):
        if value < 10000:
            raise serializers.ValidationError('Minimum donation is Rp 10.000')
        return value

    def validate(self, data):
        request_type = data.get('request_type')
        message = data.get('message', '')
        media_file = data.get('media_file')

        # text must have message
        if request_type == ScreenRequest.TYPE_TEXT and not message:
            raise serializers.ValidationError(
                {'message': 'Message is required for text requests'}
            )

        # photo/video must have file
        if request_type in (ScreenRequest.TYPE_PHOTO, ScreenRequest.TYPE_VIDEO) and not media_file:
            raise serializers.ValidationError(
                {'media_file': 'File is required for photo/video requests'}
            )

        # validate file size
        if media_file:
            if request_type == ScreenRequest.TYPE_PHOTO and media_file.size > MAX_PHOTO_SIZE:
                raise serializers.ValidationError(
                    {'media_file': 'Photo size cannot exceed 10MB'}
                )
            if request_type == ScreenRequest.TYPE_VIDEO and media_file.size > MAX_VIDEO_SIZE:
                raise serializers.ValidationError(
                    {'media_file': 'Video size cannot exceed 50MB'}
                )

        # check max 5 requests per session
        session = self.context.get('session')
        count = ScreenRequest.objects.filter(
            session=session,
            status__in=[
                ScreenRequest.STATUS_PENDING,
                ScreenRequest.STATUS_APPROVED,
            ]
        ).count()
        if count >= 5:
            raise serializers.ValidationError(
                'Maximum 5 screen requests per session'
            )

        return data