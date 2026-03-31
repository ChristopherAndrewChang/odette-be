import uuid
from django.db import models
from apps.users.models import User


class Table(models.Model):
    number = models.PositiveIntegerField(unique=True)
    is_open = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Table {self.number}"

    class Meta:
        ordering = ['number']


class TableInvite(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='invites')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Invite Table {self.table.number} ({'active' if self.is_active else 'inactive'})"

    class Meta:
        ordering = ['-created_at']


class CustomerSession(models.Model):
    invite = models.OneToOneField(
        TableInvite,
        on_delete=models.CASCADE,
        related_name='session',
        null=True,
        blank=True
    )
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='sessions')
    customer_name = models.CharField(max_length=100)
    session_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.customer_name} @ Table {self.table.number}"