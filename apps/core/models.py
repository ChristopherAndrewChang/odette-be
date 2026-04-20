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
    DAY_WEEKDAY = 'weekday'
    DAY_WEEKEND = 'weekend'
    DAY_CHOICES = [(DAY_WEEKDAY, 'Weekday'), (DAY_WEEKEND, 'Weekend')]

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

    day_type = models.CharField(max_length=10, choices=DAY_CHOICES)
    request_type = models.CharField(max_length=20, choices=REQUEST_CHOICES)
    min_amount = models.PositiveIntegerField()
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('day_type', 'request_type')

    def __str__(self):
        return f"{self.day_type} | {self.request_type} → Rp {self.min_amount:,}"