from django.db import models

from django.conf import settings

from orders.models import Order


# =====================================
# ORDER HISTORY LOG
# =====================================

class OrderHistoryLog(models.Model):

    order = models.ForeignKey(

        Order,

        on_delete=models.CASCADE,

        related_name='history_logs'

    )

    message = models.TextField()

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    def __str__(self):

        return (

            f'Order #{self.order.id} '

            f'- '

            f'{self.message}'

        )


# =====================================
# ACTION AUDIT LOG
# =====================================

class ActionAuditLog(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    model_name = models.CharField(
        max_length=120
    )

    object_id = models.CharField(
        max_length=120,
        blank=True,
        null=True
    )

    action = models.CharField(
        max_length=40,
        default='save'
    )

    summary = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f'{self.model_name} #{self.object_id} - {self.action}'


# =====================================
# COMPLAINT LOG
# =====================================

class Complaint(models.Model):

    table = models.ForeignKey(
        'orders.Table',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints'
    )

    description = models.TextField()

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_complaints'
    )

    is_resolved = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):

        return f'Complaint #{self.id}'
