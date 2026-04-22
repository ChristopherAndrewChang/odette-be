from django.db import models
from apps.tables.models import CustomerSession
from apps.users.models import User


class ScreenRequest(models.Model):
    TYPE_RUNNING_TEXT = 'running_text'
    TYPE_VTRON_TEXT = 'vtron_text'
    TYPE_VTRON_PHOTO = 'vtron_photo'
    TYPE_VTRON_VIDEO = 'vtron_video'
    TYPE_CHOICES = [
        (TYPE_RUNNING_TEXT, 'Running Text'),
        (TYPE_VTRON_TEXT, 'Vtron Text'),
        (TYPE_VTRON_PHOTO, 'Vtron Photo'),
        (TYPE_VTRON_VIDEO, 'Vtron Video'),
    ]

    STATUS_PENDING_REVIEW  = 'pending_review'
    STATUS_PENDING_PAYMENT = 'pending_payment'
    STATUS_PAID            = 'paid'
    STATUS_PLAYED          = 'played'
    STATUS_REJECTED        = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING_REVIEW,  'Pending Review'),
        (STATUS_PENDING_PAYMENT, 'Pending Payment'),
        (STATUS_PAID,            'Paid'),
        (STATUS_PLAYED,          'Played'),
        (STATUS_REJECTED,        'Rejected'),
    ]

    session = models.ForeignKey(
        CustomerSession,
        on_delete=models.CASCADE,
        related_name='screen_requests'
    )
    request_type = models.CharField(max_length=25, choices=TYPE_CHOICES)
    message = models.TextField(blank=True)
    media_file = models.FileField(upload_to='screen_requests/', blank=True, null=True)
    donation_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING_REVIEW)
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_screen_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    played_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='played_screen_requests'
    )
    played_at = models.DateTimeField(null=True, blank=True)
    payment_link = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.request_type} — {self.session.customer_name} @ Table {self.session.table.number}"

    class Meta:
        ordering = ['-created_at']