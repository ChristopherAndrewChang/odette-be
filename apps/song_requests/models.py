from django.db import models
from apps.tables.models import CustomerSession
from apps.users.models import User


class SongRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_INVALID = 'invalid'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_INVALID, 'Invalid'),
    ]

    session = models.ForeignKey(
        CustomerSession,
        on_delete=models.CASCADE,
        related_name='song_requests'
    )
    song_title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200, blank=True)
    donation_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_song_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.song_title} — {self.session.customer_name} @ Table {self.session.table.number}"

    class Meta:
        ordering = ['-created_at']