from django.db import models

from django.conf import settings

from restaurants.models import Restaurant
from restaurants.models import Branch


# =========================
# ROLE
# =========================

class Role(models.Model):

    restaurant = models.ForeignKey(

        Restaurant,

        on_delete=models.CASCADE,

        related_name='roles'

    )

    name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.name


# =========================
# PERMISSION
# =========================

class Permission(models.Model):

    MODULE_CHOICES = [

        ('pos', 'POS'),
        ('kitchen', 'Kitchen'),
        ('inventory', 'Inventory'),
        ('billing', 'Billing'),
        ('hr', 'HR'),
        ('analytics', 'Analytics'),
        ('settings', 'Settings'),

    ]

    ACTION_CHOICES = [

        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),

    ]

    module = models.CharField(
        max_length=50,
        choices=MODULE_CHOICES
    )

    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES
    )

    code = models.CharField(
        max_length=100,
        unique=True
    )

    def __str__(self):

        return (

            f'{self.module} '

            f'- '

            f'{self.action}'

        )


# =========================
# ROLE PERMISSION
# =========================

class RolePermission(models.Model):

    role = models.ForeignKey(

        Role,

        on_delete=models.CASCADE,

        related_name='permissions'

    )

    permission = models.ForeignKey(

        Permission,

        on_delete=models.CASCADE

    )

   