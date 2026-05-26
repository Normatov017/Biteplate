from django.db import models

from simple_history.models import HistoricalRecords


# =========================
# PAYMENT MODEL
# =========================

class Payment(models.Model):

    METHOD_CHOICES = [

        ('cash', 'Cash'),

        ('card', 'Card'),

        ('click', 'Click'),

        ('payme', 'Payme'),

        ('uzum', 'Uzum'),

        ('split', 'Split'),

    ]


    STATUS_CHOICES = [

        ('pending', 'Pending'),

        ('paid', 'Paid'),

        ('refunded', 'Refunded'),

        ('failed', 'Failed'),

    ]


    order = models.ForeignKey(

        'orders.Order',

        on_delete=models.CASCADE,

        related_name='payments'

    )

    amount = models.DecimalField(

        max_digits=12,

        decimal_places=2

    )

    method = models.CharField(

        max_length=20,

        choices=METHOD_CHOICES

    )

    status = models.CharField(

        max_length=20,

        choices=STATUS_CHOICES,

        default='paid'

    )

    transaction_id = models.CharField(

        max_length=255,

        blank=True,

        null=True

    )

    provider_response = models.JSONField(

        blank=True,

        null=True

    )

    paid_by = models.CharField(

        max_length=255,

        blank=True,

        null=True

    )

    refunded_amount = models.DecimalField(

        max_digits=12,

        decimal_places=2,

        default=0

    )

    notes = models.TextField(

        blank=True,

        null=True

    )

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    updated_at = models.DateTimeField(

        auto_now=True

    )

    history = HistoricalRecords()


    @property
    def is_successful(self):

        return self.status == 'paid'


    def __str__(self):

        return (

            f'Payment #{self.id} '

            f'- '

            f'{self.method.upper()}'

        )