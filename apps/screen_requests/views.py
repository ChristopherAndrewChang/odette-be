from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.users.permissions import IsStaff
from apps.tables.models import CustomerSession
from apps.core.pagination import StandardPagination
from .models import ScreenRequest
from .serializers import ScreenRequestSerializer, ScreenRequestCreateSerializer

from datetime import datetime
from apps.core.utils import get_session_date, get_session_range


class ScreenRequestListView(APIView):
    """Staff sees all requests. Customers see only their own."""

    def get_permissions(self):
        return [AllowAny()]

    def get(self, request):
        session_token = request.headers.get('X-Session-Token')

        if session_token:
            try:
                session = CustomerSession.objects.get(
                    session_token=session_token,
                    is_active=True
                )
            except CustomerSession.DoesNotExist:
                return Response(
                    {'error': 'Invalid or expired session'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            requests = ScreenRequest.objects.filter(session=session)

        elif request.user.is_authenticated and hasattr(request.user, 'role'):
            requests = ScreenRequest.objects.select_related(
                'session__table'
            ).all()

            status_filter = request.query_params.get('status')
            if status_filter:
                requests = requests.filter(status=status_filter)

            request_type_filter = request.query_params.get('request_type')
            if request_type_filter:
                requests = requests.filter(request_type=request_type_filter)

            date_param = request.query_params.get('date')
            show_all = request.query_params.get('all')

            if show_all:
                pass
            elif date_param:
                try:
                    session_date = datetime.strptime(date_param, '%Y-%m-%d').date()
                except ValueError:
                    return Response(
                        {'error': 'Invalid date format. Use YYYY-MM-DD'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                start, end = get_session_range(session_date)
                requests = requests.filter(created_at__range=(start, end))
            else:
                session_date = get_session_date(timezone.now())
                start, end = get_session_range(session_date)
                requests = requests.filter(created_at__range=(start, end))

        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        paginator = StandardPagination()
        paginated = paginator.paginate_queryset(requests, request)
        serializer = ScreenRequestSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        session_token = request.headers.get('X-Session-Token')

        if not session_token:
            return Response(
                {'error': 'Session token required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            session = CustomerSession.objects.get(
                session_token=session_token,
                is_active=True
            )
        except CustomerSession.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired session'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = ScreenRequestCreateSerializer(
            data=request.data,
            context={'session': session}
        )
        if serializer.is_valid():
            request_type = serializer.validated_data.get('request_type')

            # text types skip review, go straight to pending_payment
            if request_type in (ScreenRequest.TYPE_RUNNING_TEXT, ScreenRequest.TYPE_VTRON_TEXT):
                initial_status = ScreenRequest.STATUS_PENDING_PAYMENT
            else:
                initial_status = ScreenRequest.STATUS_PENDING_REVIEW

            screen_request = serializer.save(session=session, status=initial_status)
            return Response(
                ScreenRequestSerializer(screen_request).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScreenRequestReviewView(APIView):
    """Admin approves or rejects a photo/video request."""
    permission_classes = [IsStaff]

    def patch(self, request, pk):
        try:
            screen_request = ScreenRequest.objects.get(pk=pk)
        except ScreenRequest.DoesNotExist:
            return Response(
                {'error': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if screen_request.status != ScreenRequest.STATUS_PENDING_REVIEW:
            return Response(
                {'error': 'Only pending_review requests can be reviewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if screen_request.request_type not in (
            ScreenRequest.TYPE_VTRON_PHOTO,
            ScreenRequest.TYPE_VTRON_VIDEO
        ):
            return Response(
                {'error': 'Only photo and video requests require review'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_status = request.data.get('status')
        if new_status not in (ScreenRequest.STATUS_PENDING_PAYMENT, ScreenRequest.STATUS_REJECTED):
            return Response(
                {'error': 'Status must be pending_payment or rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        screen_request.status = new_status
        screen_request.reviewed_by = request.user
        screen_request.reviewed_at = timezone.now()
        screen_request.save()

        return Response(ScreenRequestSerializer(screen_request).data)


class ScreenRequestMarkPlayedView(APIView):
    """Admin marks a paid request as played."""
    permission_classes = [IsStaff]

    def patch(self, request, pk):
        try:
            screen_request = ScreenRequest.objects.get(pk=pk)
        except ScreenRequest.DoesNotExist:
            return Response(
                {'error': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if screen_request.status != ScreenRequest.STATUS_PAID:
            return Response(
                {'error': 'Only paid requests can be marked as played'},
                status=status.HTTP_400_BAD_REQUEST
            )

        screen_request.status = ScreenRequest.STATUS_PLAYED
        screen_request.played_by = request.user
        screen_request.played_at = timezone.now()
        screen_request.save()

        return Response(ScreenRequestSerializer(screen_request).data)


class ScreenRequestDownloadView(APIView):
    """Staff downloads media file for a screen request."""
    permission_classes = [IsStaff]

    def get(self, request, pk):
        try:
            screen_request = ScreenRequest.objects.get(pk=pk)
        except ScreenRequest.DoesNotExist:
            return Response(
                {'error': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not screen_request.media_file:
            return Response(
                {'error': 'No media file for this request'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'file_url': request.build_absolute_uri(screen_request.media_file.url),
            'request_type': screen_request.request_type,
            'customer_name': screen_request.session.customer_name,
            'table_number': screen_request.session.table.number,
        })