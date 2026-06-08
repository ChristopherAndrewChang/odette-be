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
        from collections import defaultdict, Counter
        from zoneinfo import ZoneInfo

        TZ = ZoneInfo('Asia/Jakarta')

        def session_date_of(dt):
            local = dt.astimezone(TZ)
            if local.hour < 12:
                return (local - timedelta(days=1)).date()
            return local.date()

        period_map = {'7d': 7, '14d': 14, '30d': 30, '180d': 180, '365d': 365}
        date_param = request.query_params.get('date')
        period_param = request.query_params.get('period', '7d')

        if date_param:
            try:
                from datetime import datetime as dt_
                session_date = dt_.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            session_dates = [session_date]
            nights_count = 1
            period_label = 'date'
        else:
            if period_param not in period_map:
                return Response({'error': 'Invalid period'}, status=status.HTTP_400_BAD_REQUEST)
            nights_count = period_map[period_param]
            today_session = get_session_date(timezone.now())
            session_dates = [
                today_session - timedelta(days=i)
                for i in range(nights_count - 1, -1, -1)
            ]
            period_label = period_param

        if nights_count <= 30:
            group_by = 'daily'
        elif nights_count <= 180:
            group_by = 'weekly'
        else:
            group_by = 'monthly'

        start_overall, _ = get_session_range(session_dates[0])
        _, end_overall = get_session_range(session_dates[-1])

        all_songs_qs = list(
            SongRequest.objects
            .filter(created_at__range=(start_overall, end_overall))
            .values('created_at', 'donation_amount', 'status', 'song_title', 'artist')
        )
        all_screens_qs = list(
            ScreenRequest.objects
            .filter(created_at__range=(start_overall, end_overall))
            .values('created_at', 'donation_amount', 'status', 'request_type')
        )

        songs_by_date = defaultdict(list)
        for s in all_songs_qs:
            songs_by_date[session_date_of(s['created_at'])].append(s)

        screens_by_date = defaultdict(list)
        for s in all_screens_qs:
            screens_by_date[session_date_of(s['created_at'])].append(s)

        def song_rev_from(songs):
            return sum(
                float(s['donation_amount']) for s in songs
                if s['status'] == SongRequest.STATUS_DJ_APPROVED
            )

        def screen_rev_from(screens):
            return sum(
                float(s['donation_amount']) for s in screens
                if s['status'] in (ScreenRequest.STATUS_PAID, ScreenRequest.STATUS_PLAYED)
            )

        def build_bucket(key, songs, screens):
            sr = song_rev_from(songs)
            scr = screen_rev_from(screens)
            return {
                'label': key,
                'song_revenue': sr,
                'screen_revenue': scr,
                'total': sr + scr,
                'song_count': len(songs),
                'screen_count': len(screens),
                'song_approved': sum(1 for s in songs if s['status'] == SongRequest.STATUS_DJ_APPROVED),
                'screen_paid': sum(1 for s in screens if s['status'] in (ScreenRequest.STATUS_PAID, ScreenRequest.STATUS_PLAYED)),
            }

        if group_by == 'daily':
            nightly = [
                build_bucket(str(sd), songs_by_date.get(sd, []), screens_by_date.get(sd, []))
                for sd in session_dates
            ]
        else:
            bucket_songs = defaultdict(list)
            bucket_screens = defaultdict(list)
            for sd in session_dates:
                key = f"{sd.isocalendar()[0]}-W{sd.isocalendar()[1]:02d}" if group_by == 'weekly' else sd.strftime('%Y-%m')
                bucket_songs[key].extend(songs_by_date.get(sd, []))
                bucket_screens[key].extend(screens_by_date.get(sd, []))
            nightly = [
                build_bucket(k, bucket_songs[k], bucket_screens[k])
                for k in sorted(bucket_songs.keys() | bucket_screens.keys())
            ]

        total_song_rev = song_rev_from(all_songs_qs)
        total_screen_rev = screen_rev_from(all_screens_qs)
        total_rev = total_song_rev + total_screen_rev
        avg_per_night = round(total_rev / nights_count) if nights_count else 0

        song_requests = {
            'total': len(all_songs_qs),
            'dj_approved': sum(1 for s in all_songs_qs if s['status'] == SongRequest.STATUS_DJ_APPROVED),
            'dj_rejected': sum(1 for s in all_songs_qs if s['status'] == SongRequest.STATUS_DJ_REJECTED),
            'admin_approved': sum(1 for s in all_songs_qs if s['status'] == SongRequest.STATUS_ADMIN_APPROVED),
            'admin_rejected': sum(1 for s in all_songs_qs if s['status'] == SongRequest.STATUS_ADMIN_REJECTED),
            'pending': sum(1 for s in all_songs_qs if s['status'] == SongRequest.STATUS_PENDING),
        }

        screen_requests = {
            'total': len(all_screens_qs),
            'paid': sum(1 for s in all_screens_qs if s['status'] == ScreenRequest.STATUS_PAID),
            'played': sum(1 for s in all_screens_qs if s['status'] == ScreenRequest.STATUS_PLAYED),
            'rejected': sum(1 for s in all_screens_qs if s['status'] == ScreenRequest.STATUS_REJECTED),
            'pending_review': sum(1 for s in all_screens_qs if s['status'] == ScreenRequest.STATUS_PENDING_REVIEW),
        }

        screen_types = {}
        for type_key, type_name in [
            (ScreenRequest.TYPE_RUNNING_TEXT, 'Running Text'),
            (ScreenRequest.TYPE_VTRON_TEXT, 'Vtron Text'),
            (ScreenRequest.TYPE_VTRON_PHOTO, 'Vtron Photo'),
            (ScreenRequest.TYPE_VTRON_VIDEO, 'Vtron Video'),
        ]:
            paid = [
                s for s in all_screens_qs
                if s['request_type'] == type_key
                and s['status'] in (ScreenRequest.STATUS_PAID, ScreenRequest.STATUS_PLAYED)
            ]
            screen_types[type_key] = {
                'name': type_name,
                'count': len(paid),
                'revenue': sum(float(s['donation_amount']) for s in paid),
            }

        song_counter = Counter(
            (s['song_title'], s['artist'])
            for s in all_songs_qs
            if s['status'] == SongRequest.STATUS_DJ_APPROVED
        )
        top_songs = [
            {'song_title': t, 'artist': a, 'count': c}
            for (t, a), c in song_counter.most_common(5)
        ]

        best_night = max(nightly, key=lambda x: x['total']) if nightly else None

        return Response({
            'period': period_label,
            'nights': nights_count,
            'group_by': group_by,
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