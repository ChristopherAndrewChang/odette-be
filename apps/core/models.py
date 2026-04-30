from django.db import models
from apps.users.models import User

# Create your models here.

class ClubSettings(models.Model):
    song_request_enabled = models.BooleanField(default=True)
    screen_request_enabled = models.BooleanField(default=True)
    menu_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Club Settings'

    def __str__(self):
        return 'Club Settings'

    @classmethod
    def get_settings(cls):
        """Always returns the single settings instance."""
        settings, _ = cls.objects.get_or_create(id=1)
        return settings


class DonationSetting(models.Model):
    REQUEST_SONG = 'song_request'
    REQUEST_RUNNING = 'running_text'
    REQUEST_VTRON_TEXT = 'vtron_text'
    REQUEST_VTRON_PHOTO = 'vtron_photo'
    REQUEST_VTRON_VIDEO = 'vtron_video'
    REQUEST_CHOICES = [
        (REQUEST_SONG, 'Song Request'),
        (REQUEST_RUNNING, 'Running Text'),
        (REQUEST_VTRON_TEXT, 'Vtron Text'),
        (REQUEST_VTRON_PHOTO, 'Vtron Photo'),
        (REQUEST_VTRON_VIDEO, 'Vtron Video'),
    ]

    request_type = models.CharField(max_length=20, choices=REQUEST_CHOICES)
    name = models.CharField(max_length=100)
    min_amount = models.PositiveIntegerField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('request_type', 'name')

    def __str__(self):
        return f"{self.request_type} — {self.name} — Rp {self.min_amount:,}"


class BannedWord(models.Model):
    word = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word

    class Meta:
        ordering = ['word']