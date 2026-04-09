from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from apps.users.permissions import IsStaff
from .models import ClubSettings
from .serializers import ClubSettingsSerializer


class ClubSettingsView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsStaff()]

    def get(self, request):
        """Anyone can read settings — frontend uses this on scan."""
        settings = ClubSettings.get_settings()
        serializer = ClubSettingsSerializer(settings)
        return Response(serializer.data)

    def patch(self, request):
        """Only staff can update settings."""
        settings = ClubSettings.get_settings()
        serializer = ClubSettingsSerializer(
            settings, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)