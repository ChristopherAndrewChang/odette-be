from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_SUPERUSER = 'superuser'
    ROLE_ADMIN = 'admin'
    ROLE_DJ = 'dj'
    ROLE_CASHIER = 'cashier'
    ROLE_CHOICES = [
        (ROLE_SUPERUSER, 'Superuser'),
        (ROLE_ADMIN, 'Admin'),
        (ROLE_DJ, 'DJ'),
        (ROLE_CASHIER, 'Cashier'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_ADMIN)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_superuser_role(self):
        return self.role == self.ROLE_SUPERUSER

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN