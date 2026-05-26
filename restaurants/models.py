from django.db import models


# =========================
# RESTAURANT
# =========================

class Restaurant(models.Model):

    name = models.CharField(
        max_length=255
    )

    slug = models.SlugField(
        unique=True
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    currency = models.CharField(
        max_length=10,
        default='UZS'
    )

    timezone = models.CharField(
        max_length=100,
        default='Asia/Tashkent'
    )

    language = models.CharField(
        max_length=20,
        default='uz'
    )

    logo = models.ImageField(
        upload_to='restaurant_logos/',
        blank=True,
        null=True
    )

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.name


# =========================
# BRANCH
# =========================

class Branch(models.Model):

    restaurant = models.ForeignKey(

        Restaurant,

        on_delete=models.CASCADE,

        related_name='branches'

    )

    name = models.CharField(
        max_length=255
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (

            f'{self.restaurant.name} '

            f'- '

            f'{self.name}'

        )
    