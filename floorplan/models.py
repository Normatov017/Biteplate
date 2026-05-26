from django.db import models

from restaurants.models import Branch


class FloorDecor(models.Model):

    TYPE_CHOICES = [
        ('wall', 'Wall'),
        ('plant', 'Plant'),
        ('bar', 'Bar'),
        ('kitchen', 'Kitchen'),
        ('door', 'Door'),
        ('note', 'Note'),
    ]

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='floor_decors',
        null=True,
        blank=True
    )

    floor_area = models.CharField(
        max_length=80,
        default='Main Floor'
    )

    decor_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        default='plant'
    )

    label = models.CharField(
        max_length=120,
        blank=True,
        null=True
    )

    pos_x = models.IntegerField(
        default=80
    )

    pos_y = models.IntegerField(
        default=80
    )

    pos_width = models.IntegerField(
        default=120
    )

    pos_height = models.IntegerField(
        default=80
    )

    def __str__(self):

        return self.label or self.get_decor_type_display()
