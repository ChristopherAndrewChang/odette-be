from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from apps.users.permissions import IsStaff
from .models import ClubSettings, DonationSetting, BannedWord
from .serializers import ClubSettingsSerializer, DonationSettingSerializer, BannedWordSerializer
from .utils import get_session_day_type
from apps.core.pagination import StandardPagination


class ClubSettingsView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsStaff()]

    def get(self, request):
        settings = ClubSettings.get_settings()
        serializer = ClubSettingsSerializer(settings)
        return Response(serializer.data)

    def patch(self, request):
        settings = ClubSettings.get_settings()
        serializer = ClubSettingsSerializer(
            settings, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DonationSettingPublicView(APIView):
    """Customer-facing — returns active minimums per request type."""
    permission_classes = [AllowAny]

    def get(self, request):
        settings = DonationSetting.objects.filter(is_active=True)
        result = {s.request_type: s.min_amount for s in settings}
        return Response(result)


class DonationSettingAdminView(APIView):
    """Admin manages donation price settings."""
    permission_classes = [IsStaff]

    def get(self, request):
        request_type = request.query_params.get('request_type')
        settings = DonationSetting.objects.all().order_by('request_type', 'name')
        if request_type:
            settings = settings.filter(request_type=request_type)
        serializer = DonationSettingSerializer(settings, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DonationSettingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DonationSettingDetailView(APIView):
    """Admin updates or deletes a price setting."""
    permission_classes = [IsStaff]

    def patch(self, request, pk):
        try:
            setting = DonationSetting.objects.get(pk=pk)
        except DonationSetting.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DonationSettingSerializer(setting, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            setting = DonationSetting.objects.get(pk=pk)
        except DonationSetting.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        setting.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DonationSettingActivateView(APIView):
    """Admin activates a price — deactivates all others of same request_type."""
    permission_classes = [IsStaff]

    def patch(self, request, pk):
        try:
            setting = DonationSetting.objects.get(pk=pk)
        except DonationSetting.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        # deactivate all others of same request_type
        DonationSetting.objects.filter(
            request_type=setting.request_type
        ).update(is_active=False)

        # activate this one
        setting.is_active = True
        setting.save(update_fields=['is_active'])

        return Response(DonationSettingSerializer(setting).data)

class BannedWordListView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        words = BannedWord.objects.all()
        paginator = StandardPagination()
        paginated = paginator.paginate_queryset(words, request)
        serializer = BannedWordSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = BannedWordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BannedWordDetailView(APIView):
    """Admin deletes a banned word."""
    permission_classes = [IsStaff]

    def delete(self, request, pk):
        try:
            word = BannedWord.objects.get(pk=pk)
        except BannedWord.DoesNotExist:
            return Response(
                {'error': 'Not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        word.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)