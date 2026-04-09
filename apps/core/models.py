from django.db import models

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