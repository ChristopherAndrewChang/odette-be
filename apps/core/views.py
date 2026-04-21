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
    """Customer-facing — returns minimums for today's session."""
    permission_classes = [AllowAny]

    def get(self, request):
        day_type = get_session_day_type()
        settings = DonationSetting.objects.filter(day_type=day_type)
        result = {s.request_type: s.min_amount for s in settings}
        return Response(result)


class DonationSettingAdminView(APIView):
    """Admin manages weekday/weekend rates."""
    permission_classes = [IsStaff]

    def get(self, request):
        settings = DonationSetting.objects.all().order_by('day_type', 'request_type')
        serializer = DonationSettingSerializer(settings, many=True)
        return Response(serializer.data)

    def patch(self, request):
        day_type = request.data.get('day_type')
        request_type = request.data.get('request_type')
        min_amount = request.data.get('min_amount')

        if not all([day_type, request_type, min_amount]):
            return Response(
                {'error': 'day_type, request_type and min_amount are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        setting, _ = DonationSetting.objects.get_or_create(
            day_type=day_type,
            request_type=request_type,
            defaults={'min_amount': min_amount}
        )
        setting.min_amount = min_amount
        setting.updated_by = request.user
        setting.save()

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