from django.db import models
from apps.tables.models import CustomerSession
from apps.users.models import User


class SongRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ADMIN_APPROVED = 'admin_approved'
    STATUS_ADMIN_REJECTED = 'admin_rejected'
    STATUS_DJ_APPROVED = 'dj_approved'
    STATUS_DJ_REJECTED = 'dj_rejected'
    STATUS_INVALID = 'invalid'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ADMIN_APPROVED, 'Approved by Admin'),
        (STATUS_ADMIN_REJECTED, 'Rejected by Admin'),
        (STATUS_DJ_APPROVED, 'Approved by DJ'),
        (STATUS_DJ_REJECTED, 'Rejected by DJ'),
        (STATUS_INVALID, 'Invalid'),
    ]

    STATUS_DISPLAY = {
        STATUS_PENDING: 'Menunggu persetujuan',
        STATUS_ADMIN_APPROVED: 'Disetujui admin, menunggu DJ',
        STATUS_ADMIN_REJECTED: 'Ditolak admin',
        STATUS_DJ_APPROVED: 'Disetujui DJ, lagu akan diputar!',
        STATUS_DJ_REJECTED: 'Ditolak DJ',
        STATUS_INVALID: 'Request tidak valid',
    }

    session = models.ForeignKey(
        CustomerSession,
        on_delete=models.CASCADE,
        related_name='song_requests'
    )
    song_title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200, blank=True)
    donation_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by_admin = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='admin_reviewed_songs'
    )
    reviewed_by_dj = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='dj_reviewed_songs'
    )
    admin_reviewed_at = models.DateTimeField(null=True, blank=True)
    dj_reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.song_title} — {self.session.customer_name} @ Table {self.session.table.number}"

    def get_status_display_id(self):
        return self.STATUS_DISPLAY.get(self.status, self.status)

    class Meta:
        ordering = ['-created_at']