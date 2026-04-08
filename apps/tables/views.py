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


def generate_qr_receipt_image(table_number, token):
    """Generate a single receipt PNG sized for 58mm thermal printer."""
    from PIL import Image, ImageDraw, ImageFont
    import urllib.request
    import os

    width = 464  # 58mm at 203dpi
    today = timezone.localtime(timezone.now()).date()
    table_on_top = today.day % 2 != 0
    date_str = today.strftime("%d %b %Y")

    # generate QR
    scan_url = f"{settings.FRONTEND_URL}/user/scan?token={token}"
    qr = qrcode.QRCode(box_size=6, border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(scan_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_size = width - 40
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

    # find font
    font_paths_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    font_paths_regular = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]

    font_large = None
    font_small = None

    for path in font_paths_bold:
        if os.path.exists(path):
            font_large = ImageFont.truetype(path, 52)
            break

    for path in font_paths_regular:
        if os.path.exists(path):
            font_small = ImageFont.truetype(path, 26)
            break

    if not font_large:
        font_large = ImageFont.load_default(size=52)
    if not font_small:
        font_small = ImageFont.load_default(size=26)

    padding = 20
    text_area = 80
    date_area = 40
    total_height = text_area + qr_size + date_area + padding * 2

    img = Image.new("RGB", (width, total_height), "white")
    draw = ImageDraw.Draw(img)

    table_text = f"TABLE {table_number}"
    scan_text = "Scan for interactive menu"

    def center_text(text, font, y, color="black"):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((width - w) // 2, y), text, fill=color, font=font)

    if table_on_top:
        # table number top
        center_text(table_text, font_large, padding)
        # QR below table number
        img.paste(qr_img, ((width - qr_size) // 2, text_area))
        # scan text below QR
        center_text(scan_text, font_small, text_area + qr_size + 8, color="#555555")
        # date at very bottom
        center_text(date_str, font_small, text_area + qr_size + 40, color="#AAAAAA")
    else:
        # QR on top
        img.paste(qr_img, ((width - qr_size) // 2, padding))
        # scan text below QR
        center_text(scan_text, font_small, padding + qr_size + 8, color="#555555")
        # table number at bottom
        center_text(table_text, font_large, padding + qr_size + 40)
        # date at very bottom
        center_text(date_str, font_small, padding + qr_size + 100, color="#AAAAAA")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG', dpi=(203, 203))
    buffer.seek(0)
    return buffer


def generate_qr_pdf(tables_with_tokens):
    from datetime import date
    buffer = io.BytesIO()

    receipt_width = 58 * mm
    receipt_height = 80 * mm
    total_height = len(tables_with_tokens) * receipt_height

    c = canvas.Canvas(buffer, pagesize=(receipt_width, total_height))

    today = timezone.localtime(timezone.now()).date()
    date_str = today.strftime("%d %b %Y")
    table_on_top = today.day % 2 != 0

    for idx, (table_number, token) in enumerate(tables_with_tokens):
        y_start = total_height - (idx + 1) * receipt_height

        # QR code
        qr_size = 40 * mm
        qr_img = generate_qr_image(token, table_number)
        qr_x = (receipt_width - qr_size) / 2
        qr_y = y_start + (receipt_height - qr_size) / 2 - 5 * mm
        c.drawImage(ImageReader(qr_img), qr_x, qr_y, qr_size, qr_size)

        # table number — top or bottom based on day
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        if table_on_top:
            c.drawCentredString(receipt_width / 2, qr_y + qr_size + 4 * mm, f"TABLE {table_number}")
        else:
            c.drawCentredString(receipt_width / 2, qr_y - 5 * mm, f"TABLE {table_number}")

        # instruction — opposite side of table number
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        if table_on_top:
            c.drawCentredString(receipt_width / 2, qr_y - 5 * mm, "Scan for interactive menu")
        else:
            c.drawCentredString(receipt_width / 2, qr_y + qr_size + 4 * mm, "Scan for interactive menu")

        # date at very bottom — small
        c.setFont("Helvetica", 6)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawCentredString(receipt_width / 2, y_start + 2 * mm, date_str)

        # dotted tear line
        if idx < len(tables_with_tokens) - 1:
            c.setStrokeColorRGB(0.6, 0.6, 0.6)
            c.setLineWidth(0.3)
            c.setDash(2, 2)
            c.line(2 * mm, y_start, receipt_width - 2 * mm, y_start)
            c.setDash()

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
    """Generate QR for a single table — returns PNG image."""
    permission_classes = [IsStaff]

    def post(self, request, pk):
        table = Table.objects.filter(pk=pk, is_active=True).first()

        if not table:
            return Response(
                {'error': 'Table not found or inactive'},
                status=status.HTTP_404_NOT_FOUND
            )

        TableInvite.objects.filter(table=table, is_active=True).update(is_active=False)
        invite = TableInvite.objects.create(table=table, created_by=request.user)

        img_buffer = generate_qr_receipt_image(table.number, str(invite.token))

        response = HttpResponse(img_buffer, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="table_{table.number}.png"'
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

        receipt_width = 58 * mm
        receipt_height = 80 * mm

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(receipt_width, receipt_height))

        today = timezone.localtime(timezone.now()).date()
        table_on_top = today.day % 2 != 0
        date_str = today.strftime("%d %b %Y")

        qr_size = 42 * mm  # changed from 46
        qr_x = (receipt_width - qr_size) / 2

        for idx, table in enumerate(tables):
            invite = TableInvite.objects.create(
                table=table,
                created_by=request.user
            )

            qr_img = generate_qr_image(table.number, str(invite.token))

            if table_on_top:
                # TABLE NUMBER — top
                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica-Bold", 11)
                c.drawCentredString(receipt_width / 2, receipt_height - 9 * mm, f"TABLE {table.number}")

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
                c.drawCentredString(receipt_width / 2, qr_y - 8 * mm, f"TABLE {table.number}")

            # new page for each table
            if idx < len(tables) - 1:
                c.showPage()
                c.setPageSize((receipt_width, receipt_height))

        c.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="all_tables_qr.pdf"'
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