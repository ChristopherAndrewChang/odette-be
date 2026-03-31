from rest_framework import serializers
from .models import ClubSettings


class ClubSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubSettings
        fields = [
            'song_request_enabled',
            'screen_request_enabled',
            'menu_enabled',
        ]