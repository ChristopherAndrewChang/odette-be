import qrcode
import io
import zipfile
from django.utils import timezone
from django.utils.timezone import localtime
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from apps.users.permissions import IsStaff
from .models import Table, TableInvite, CustomerSession
from .serializers import (
    TableSerializer, BulkTableSerializer,
    CustomerSessionSerializer, ScanQRSerializer
)
from apps.core.pagination import StandardPagination


def get_expiry():
    now = localtime(timezone.now())
    expiry = now.replace(hour=4, minute=0, second=0, microsecond=0)
    if now >= expiry:
        expiry += timedelta(days=1)
    return expiry


def generate_qr_image(token, table_number):
    """Generate QR code image as BytesIO."""
    scan_url = f"{settings.FRONTEND_URL}/user/scan?token={token}"
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(scan_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


def generate_qr_receipt_pdf(table_number, token):
    """Generate a single receipt PDF sized for 58mm thermal printer."""
    today = timezone.localtime(timezone.now()).date()
    table_on_top = today.day % 2 != 0
    date_str = today.strftime("%d %b %Y")

    receipt_width = 58 * mm
    receipt_height = 60 * mm

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(receipt_width, receipt_height))

    qr_size = 20 * mm
    qr_x = (receipt_width - qr_size) / 2
    qr_img = generate_qr_image(token, table_number)

    if table_on_top:
        # TABLE NUMBER — top
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(receipt_width / 2, receipt_height - 9 * mm, f"TABLE {table_number}")

        # QR — middle
        qr_y = receipt_height - 11 * mm - qr_size
        c.drawImage(ImageReader(qr_img), qr_x, qr_y, qr_size, qr_size)

        # scan text
        c.setFont("Helvetica", 6)
        c.setFillColorRGB(0.35, 0.35, 0.35)
        c.drawCentredString(receipt_width / 2, qr_y - 5 * mm, "Scan for interactive menu")

        # date — bottom
        c.setFont("Helvetica", 5)
        c.setFillColorRGB(0.65, 0.65, 0.65)
        c.drawCentredString(receipt_width / 2, qr_y - 9 * mm, date_str)

    else:
        # date — top
        c.setFont("Helvetica", 5)
        c.setFillColorRGB(0.65, 0.65, 0.65)
        c.drawCentredString(receipt_width / 2, receipt_height - 6 * mm, date_str)

        # scan text
        c.setFont("Helvetica", 6)
        c.setFillColorRGB(0.35, 0.35, 0.35)
        c.drawCentredString(receipt_width / 2, receipt_height - 10 * mm, "Scan for interactive menu")

        # QR — middle
        qr_y = receipt_height - 13 * mm - qr_size
        c.drawImage(ImageReader(qr_img), qr_x, qr_y, qr_size, qr_size)

        # TABLE NUMBER — bottom
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(receipt_width / 2, qr_y - 8 * mm, f"TABLE {table_number}")

    c.save()
    buffer.seek(0)
    return buffer


def generate_qr_bulk_pdf(tables_data):
    """Generate multi-page PDF, one QR per page for thermal printing."""
    today = timezone.localtime(timezone.now()).date()
    table_on_top = today.day % 2 != 0
    date_str = today.strftime("%d %b %Y")

    receipt_width = 58 * mm
    receipt_height = 60 * mm

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(receipt_width, receipt_height))

    qr_size = 20 * mm
    qr_x = (receipt_width - qr_size) / 2

    for idx, (table_number, token) in enumerate(tables_data):
        qr_img = generate_qr_image(token, table_number)

        if table_on_top:
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(receipt_width / 2, receipt_height - 9 * mm, f"TABLE {table_number}")

            qr_y = receipt_height - 11 * mm - qr_size
            c.drawImage(ImageReader(qr_img), qr_x, qr_y, qr_size, qr_size)

            c.setFont("Helvetica", 6)
            c.setFillColorRGB(0.35, 0.35, 0.35)
            c.drawCentredString(receipt_width / 2, qr_y - 5 * mm, "Scan for interactive menu")

            c.setFont("Helvetica", 5)
            c.setFillColorRGB(0.65, 0.65, 0.65)
            c.drawCentredString(receipt_width / 2, qr_y - 9 * mm, date_str)

        else:
            c.setFont("Helvetica", 5)
            c.setFillColorRGB(0.65, 0.65, 0.65)
            c.drawCentredString(receipt_width / 2, receipt_height - 6 * mm, date_str)

            c.setFont("Helvetica", 6)
            c.setFillColorRGB(0.35, 0.35, 0.35)
            c.drawCentredString(receipt_width / 2, receipt_height - 10 * mm, "Scan for interactive menu")

            qr_y = receipt_height - 13 * mm - qr_size
            c.drawImage(ImageReader(qr_img), qr_x, qr_y, qr_size, qr_size)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(receipt_width / 2, qr_y - 8 * mm, f"TABLE {table_number}")

        if idx < len(tables_data) - 1:
            c.showPage()
            c.setPageSize((receipt_width, receipt_height))

    c.save()
    buffer.seek(0)
    return buffer


class TableListCreateView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        tables = Table.objects.prefetch_related('sessions').all()
        paginator = StandardPagination()
        paginated = paginator.paginate_queryset(tables, request)
        serializer = TableSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = TableSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TableBulkCreateView(APIView):
    permission_classes = [IsStaff]

    def post(self, request):
        serializer = BulkTableSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        numbers = serializer.validated_data['numbers']

        if len(numbers) != len(set(numbers)):
            return Response(
                {'error': 'Duplicate table numbers in request'},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing = Table.objects.filter(number__in=numbers).values_list('number', flat=True)
        if existing:
            return Response(
                {'error': f'Table numbers already exist: {list(existing)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tables = Table.objects.bulk_create([Table(number=n) for n in numbers])
        return Response(
            TableSerializer(tables, many=True).data,
            status=status.HTTP_201_CREATED
        )


class GenerateQRView(APIView):
    """Generate QR for a single table — returns PDF."""
    permission_classes = [IsStaff]

    def post(self, request, pk):
        table = Table.objects.filter(pk=pk, is_active=True).first()

        if not table:
            return Response(
                {'error': 'Table not found or inactive'},
                status=status.HTTP_404_NOT_FOUND
            )

        TableInvite.objects.filter(table=table, is_active=True).update(is_active=False)
        CustomerSession.objects.filter(table=table, is_active=True).update(is_active=False)

        invite = TableInvite.objects.create(table=table, created_by=request.user)
        pdf_buffer = generate_qr_receipt_pdf(table.number, str(invite.token))

        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="table_{table.number}.pdf"'
        return response


class BulkGenerateQRView(APIView):
    """Generate QR for all tables — returns multi-page PDF, one QR per page."""
    permission_classes = [IsStaff]

    def post(self, request):
        tables = Table.objects.filter(is_active=True).order_by('number')

        if not tables.exists():
            return Response(
                {'error': 'No active tables found'},
                status=status.HTTP_404_NOT_FOUND
            )

        TableInvite.objects.filter(is_active=True).update(is_active=False)
        CustomerSession.objects.filter(is_active=True).update(is_active=False)

        tables_data = []
        for table in tables:
            invite = TableInvite.objects.create(
                table=table,
                created_by=request.user
            )
            tables_data.append((table.number, str(invite.token)))

        pdf_buffer = generate_qr_bulk_pdf(tables_data)

        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="all_tables_qr.pdf"'
        return response


class OpenNightView(APIView):
    permission_classes = [IsStaff]

    def post(self, request):
        Table.objects.filter(is_active=True).update(is_open=True)
        return Response({'message': 'All tables are now open'})


class CloseNightView(APIView):
    permission_classes = [IsStaff]

    def post(self, request):
        Table.objects.filter(is_active=True).update(is_open=False)
        CustomerSession.objects.filter(is_active=True).update(is_active=False)
        TableInvite.objects.filter(is_active=True).update(is_active=False)
        return Response({'message': 'All tables closed, all sessions and invites ended'})


class ScanQRView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ScanQRSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['token']
        customer_name = serializer.validated_data['customer_name']

        try:
            invite = TableInvite.objects.select_related('table').get(token=token)
        except TableInvite.DoesNotExist:
            return Response(
                {'error': 'Invalid QR code'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not invite.is_active:
            return Response(
                {'error': 'This QR code has expired, please ask staff for a new one'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not invite.table.is_active:
            return Response(
                {'error': 'This table is no longer available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not invite.table.is_open:
            return Response(
                {'error': 'This table is not open yet, please ask staff'},
                status=status.HTTP_400_BAD_REQUEST
            )

        session = CustomerSession.objects.create(
            invite=invite,
            table=invite.table,
            customer_name=customer_name,
            expires_at=get_expiry(),
        )

        return Response({
            'session_token': str(session.session_token),
            'customer_name': session.customer_name,
            'table_number': invite.table.number,
            'expires_at': session.expires_at,
        })


class TableDetailView(APIView):
    permission_classes = [IsStaff]

    def get_object(self, pk):
        return get_object_or_404(Table, pk=pk)

    def patch(self, request, pk):
        table = self.get_object(pk)
        serializer = TableSerializer(table, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        table = self.get_object(pk)
        table.is_active = False
        table.save()
        return Response(status=status.HTTP_204_NO_CONTENT)