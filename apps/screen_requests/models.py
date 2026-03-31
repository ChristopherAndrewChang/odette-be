from django.db import models
from apps.tables.models import CustomerSession
from apps.users.models import User


class ScreenRequest(models.Model):
    TYPE_TEXT = 'text'
    TYPE_PHOTO = 'photo'
    TYPE_VIDEO = 'video'
    TYPE_CHOICES = [
        (TYPE_TEXT, 'Text'),
        (TYPE_PHOTO, 'Photo'),
        (TYPE_VIDEO, 'Video'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    session = models.ForeignKey(
        CustomerSession,
        on_delete=models.CASCADE,
        related_name='screen_requests'
    )
    request_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    message = models.TextField(blank=True)
    media_file = models.FileField(upload_to='screen_requests/', blank=True, null=True)
    donation_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_screen_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.request_type} — {self.session.customer_name} @ Table {self.session.table.number}"

    class Meta:
        ordering = ['-created_at']