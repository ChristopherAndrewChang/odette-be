from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.users.permissions import IsStaff
from apps.tables.models import CustomerSession
from apps.core.pagination import StandardPagination
from .models import SongRequest
from .serializers import SongRequestSerializer, SongRequestCreateSerializer


class SongRequestListView(APIView):
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
            requests = SongRequest.objects.filter(session=session)

        elif request.user.is_authenticated and hasattr(request.user, 'role'):
            requests = SongRequest.objects.select_related(
                'session__table'
            ).all()

            if request.user.role == 'dj':
                requests = requests.filter(status=SongRequest.STATUS_APPROVED)
            else:
                status_filter = request.query_params.get('status')
                if status_filter:
                    requests = requests.filter(status=status_filter)

                date_filter = request.query_params.get('date')
                show_all = request.query_params.get('all')

                if show_all:
                    pass
                elif date_filter:
                    requests = requests.filter(created_at__date=date_filter)
                else:
                    requests = requests.filter(
                        created_at__date=timezone.now().date()
                    )

        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        paginator = StandardPagination()
        paginated = paginator.paginate_queryset(requests, request)
        serializer = SongRequestSerializer(paginated, many=True)
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

        serializer = SongRequestCreateSerializer(
            data=request.data,
            context={'session': session}
        )
        if serializer.is_valid():
            song_request = serializer.save(session=session)
            return Response(
                SongRequestSerializer(song_request).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SongRequestReviewView(APIView):
    """Staff approves or rejects a request."""
    permission_classes = [IsStaff]

    def patch(self, request, pk):
        try:
            song_request = SongRequest.objects.get(pk=pk)
        except SongRequest.DoesNotExist:
            return Response(
                {'error': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get('status')
        if new_status not in (SongRequest.STATUS_APPROVED, SongRequest.STATUS_REJECTED):
            return Response(
                {'error': 'Status must be approved or rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        song_request.status = new_status
        song_request.reviewed_by = request.user
        song_request.reviewed_at = timezone.now()
        song_request.save()

        return Response(SongRequestSerializer(song_request).data)