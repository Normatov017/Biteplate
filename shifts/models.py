from django.db import models

from django.conf import settings

from restaurants.models import Restaurant
from restaurants.models import Branch


# =========================
# SHIFT
# =========================

class Shift(models.Model):

    STATUS_CHOICES = [

        ('open', 'Open'),

        ('closed', 'Closed'),

    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cashier_shifts'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )

    opening_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    closing_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    expected_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_sales = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_orders = models.IntegerField(
        default=0
    )

    difference = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    opened_at = models.DateTimeField(
        auto_now_add=True
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True
    )


    # =========================
    # CLOSE SHIFT
    # =========================

    def close_shift(self, actual_cash):

        self.closing_cash = actual_cash

        self.difference = (

            actual_cash -
            self.expected_cash

        )

        self.status = 'closed'

        from django.utils import timezone

        self.closed_at = timezone.now()

        self.save()


    def __str__(self):

        return (

            f'Shift #{self.id}'
            f' - '
            f'{self.cashier}'

        )


# =========================
# SHIFT CLOCK LOG
# =========================

class ShiftLog(models.Model):

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shift_logs'
    )

    clock_in = models.DateTimeField()

    clock_out = models.DateTimeField(
        null=True,
        blank=True
    )

    note = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    def __str__(self):

        return f'{self.employee} - {self.clock_in}'


class CashMovement(models.Model):

    TYPE_CHOICES = [
        ('in', 'Cash In'),
        ('out', 'Cash Out'),
    ]

    shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name='cash_movements'
    )

    movement_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    reason = models.CharField(
        max_length=255
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def signed_amount(self):

        if self.movement_type == 'out':

            return -self.amount

        return self.amount

    def __str__(self):

        return f'{self.get_movement_type_display()} {self.amount}'
