from django.db import models
from orders.models import Table


class Reservation(models.Model):

    customer_name = models.CharField(
        max_length=100
    )

    phone_number = models.CharField(
        max_length=20
    )

    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE
    )

    reservation_time = models.DateTimeField()

    end_time = models.DateTimeField(
        null=True,
        blank=True
    )

    guest_count = models.IntegerField()

    confirmation_sent_at = models.DateTimeField(
        null=True,
        blank=True
    )

    reminder_sent_at = models.DateTimeField(
        null=True,
        blank=True
    )

    last_reminder_attempt_at = models.DateTimeField(
        null=True,
        blank=True
    )

    last_reminder_error = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('seated', 'Seated'),
            ('cancelled', 'Cancelled'),
        ],
        default='confirmed'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.customer_name
