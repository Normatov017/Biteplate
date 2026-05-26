from django.conf import settings
from django.db import models


class HeldOrder(models.Model):

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('resumed', 'Resumed'),
        ('cancelled', 'Cancelled'),
    ]

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='held_orders'
    )

    cart = models.JSONField(
        default=dict
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    note = models.CharField(
        max_length=255,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    resumed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:

        ordering = ['-created_at']

    def __str__(self):

        return f'Held Order #{self.id}'

