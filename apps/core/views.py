from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from apps.users.permissions import IsStaff
from .models import ClubSettings, DonationSetting, BannedWord
from .serializers import ClubSettingsSerializer, DonationSettingSerializer, BannedWordSerializer
from .utils import get_session_day_type
from apps.core.pagination import StandardPagination

from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count
from apps.users.permissions import IsStaff
from apps.song_requests.models import SongRequest
from apps.screen_requests.models import ScreenRequest
from apps.core.utils import get_session_date, get_session_range


class ReportSummaryView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        period = request.query_params.get('period', '7d')
        period_map = {'1d': 1, '7d': 7, '14d': 14, '30d': 30}
        nights_count = period_map.get(period, 7)

        today_session = get_session_date(timezone.now())

        # Build list of session dates oldest → newest
        session_dates = [
            today_session - timedelta(days=i)
            for i in range(nights_count - 1, -1, -1)
        ]

        # Per-night breakdown
        nightly = []
        for session_date in session_dates:
            start, end = get_session_range(session_date)

            songs = SongRequest.objects.filter(created_at__range=(start, end))
            screens = ScreenRequest.objects.filter(created_at__range=(start, end))

            song_rev = songs.filter(
                status=SongRequest.STATUS_DJ_APPROVED
            ).aggregate(t=Sum('donation_amount'))['t'] or 0

            screen_rev = screens.filter(
                status__in=[ScreenRequest.STATUS_PAID, ScreenRequest.STATUS_PLAYED]
            ).aggregate(t=Sum('donation_amount'))['t'] or 0

            nightly.append({
                'date': str(session_date),
                'song_count': songs.count(),
                'screen_count': screens.count(),
                'song_approved': songs.filter(status=SongRequest.STATUS_DJ_APPROVED).count(),
                'screen_paid': screens.filter(status__in=[
                    ScreenRequest.STATUS_PAID, ScreenRequest.STATUS_PLAYED
                ]).count(),
                'song_revenue': float(song_rev),
                'screen_revenue': float(screen_rev),
                'total': float(song_rev + screen_rev),
            })

        # Totals
        total_song_rev = sum(n['song_revenue'] for n in nightly)
        total_screen_rev = sum(n['screen_revenue'] for n in nightly)
        total_rev = total_song_rev + total_screen_rev
        avg_per_night = round(total_rev / nights_count) if nights_count else 0

        # Overall date range
        start_overall, _ = get_session_range(session_dates[0])
        _, end_overall = get_session_range(session_dates[-1])

        all_songs = SongRequest.objects.filter(
            created_at__range=(start_overall, end_overall)
        )
        all_screens = ScreenRequest.objects.filter(
            created_at__range=(start_overall, end_overall)
        )

        # Song status breakdown
        song_requests = {
            'total': all_songs.count(),
            'dj_approved': all_songs.filter(status=SongRequest.STATUS_DJ_APPROVED).count(),
            'dj_rejected': all_songs.filter(status=SongRequest.STATUS_DJ_REJECTED).count(),
            'admin_approved': all_songs.filter(status=SongRequest.STATUS_ADMIN_APPROVED).count(),
            'admin_rejected': all_songs.filter(status=SongRequest.STATUS_ADMIN_REJECTED).count(),
            'pending': all_songs.filter(status=SongRequest.STATUS_PENDING).count(),
        }

        # Screen status breakdown
        screen_requests = {
            'total': all_screens.count(),
            'paid': all_screens.filter(status=ScreenRequest.STATUS_PAID).count(),
            'played': all_screens.filter(status=ScreenRequest.STATUS_PLAYED).count(),
            'rejected': all_screens.filter(status=ScreenRequest.STATUS_REJECTED).count(),
            'pending_review': all_screens.filter(status=ScreenRequest.STATUS_PENDING_REVIEW).count(),
        }

        # Screen type breakdown
        screen_types = {}
        for type_key, type_name in [
            (ScreenRequest.TYPE_RUNNING_TEXT, 'Running Text'),
            (ScreenRequest.TYPE_VTRON_TEXT, 'Vtron Text'),
            (ScreenRequest.TYPE_VTRON_PHOTO, 'Vtron Photo'),
            (ScreenRequest.TYPE_VTRON_VIDEO, 'Vtron Video'),
        ]:
            qs = all_screens.filter(
                request_type=type_key,
                status__in=[ScreenRequest.STATUS_PAID, ScreenRequest.STATUS_PLAYED]
            )
            screen_types[type_key] = {
                'name': type_name,
                'count': qs.count(),
                'revenue': float(qs.aggregate(t=Sum('donation_amount'))['t'] or 0),
            }

        # Top 5 songs
        top_songs = list(
            all_songs
            .filter(status=SongRequest.STATUS_DJ_APPROVED)
            .values('song_title', 'artist')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        # Best night
        best_night = max(nightly, key=lambda x: x['total']) if nightly else None

        return Response({
            'period': period,
            'nights': nights_count,
            'total_revenue': total_rev,
            'song_revenue': total_song_rev,
            'screen_revenue': total_screen_rev,
            'avg_per_night': avg_per_night,
            'song_requests': song_requests,
            'screen_requests': screen_requests,
            'screen_types': screen_types,
            'top_songs': top_songs,
            'nightly': nightly,
            'best_night': best_night,
        })


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