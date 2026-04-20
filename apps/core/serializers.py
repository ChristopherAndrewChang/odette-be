from rest_framework import serializers
from .models import ClubSettings, DonationSetting


class ClubSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubSettings
        fields = [
            'song_request_enabled',
            'screen_request_enabled',
            'menu_enabled',
        ]


class DonationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationSetting
        fields = ['id', 'day_type', 'request_type', 'min_amount', 'updated_at']
        read_only_fields = ['updated_at']