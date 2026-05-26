from django.db import models

from restaurants.models import Restaurant
from restaurants.models import Branch
from simple_history.models import HistoricalRecords


# =========================
# MODIFIER GROUP
# =========================

class ModifierGroup(models.Model):

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='modifier_groups',
        null=True,
        blank=True
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='modifier_groups',
        null=True,
        blank=True
    )

    name = models.CharField(
        max_length=100
    )

    required = models.BooleanField(
        default=False
    )

    multiple_choice = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    def __str__(self):

        return self.name


# =========================
# MODIFIER OPTION
# =========================

class ModifierOption(models.Model):

    group = models.ForeignKey(
        ModifierGroup,
        on_delete=models.CASCADE,
        related_name='options'
    )

    name = models.CharField(
        max_length=100
    )

    extra_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    def __str__(self):

        return self.name


# =========================
# MENU ITEM
# =========================

class MenuItem(models.Model):

    CATEGORY_CHOICES = [

        ('starter', 'Starter'),
        ('main', 'Main Course'),
        ('dessert', 'Dessert'),
        ('beverage', 'Beverage'),
        ('fast_food', 'Fast Food'),
        ('combo', 'Combo'),

    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_items',
        null=True,
        blank=True
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='menu_items',
        null=True,
        blank=True
    )

    name = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES
    )

    image = models.ImageField(
        upload_to='menu_items/',
        blank=True,
        null=True
    )

    available = models.BooleanField(
        default=True
    )

    available_from = models.TimeField(
        null=True,
        blank=True
    )

    available_to = models.TimeField(
        null=True,
        blank=True
    )

    preparation_time = models.IntegerField(
        default=10
    )

    calories = models.IntegerField(
        default=0
    )

    is_featured = models.BooleanField(
        default=False
    )

    is_spicy = models.BooleanField(
        default=False
    )

    is_vegetarian = models.BooleanField(
        default=False
    )

    modifier_groups = models.ManyToManyField(
        ModifierGroup,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True
    )

    history = HistoricalRecords()

    def __str__(self):

        return self.name


# =========================
# PRODUCT VARIANT
# =========================

class ProductVariant(models.Model):

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    name = models.CharField(
        max_length=100
    )

    extra_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    image = models.ImageField(
        upload_to='variants/',
        blank=True,
        null=True
    )

    available = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    def __str__(self):

        return f'{self.menu_item.name} - {self.name}'


# =====================================
# MENU COMPONENT (COMPOSITE BASE)
# =====================================

class MenuComponent(models.Model):

    name = models.CharField(
        max_length=255
    )

    price = models.DecimalField(

        max_digits=10,

        decimal_places=2,

        default=0

    )

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    class Meta:

        abstract = True

    def get_total_price(self):

        raise NotImplementedError(
            'Subclasses must implement this method'
        )


# =====================================
# SINGLE MENU ITEM (LEAF)
# =====================================

class SingleMenuItem(MenuComponent):

    menu_item = models.OneToOneField(

        MenuItem,

        on_delete=models.CASCADE,

        related_name='single_component'

    )

    def get_total_price(self):

        return self.menu_item.price

    def __str__(self):

        return (

            f'Single: '

            f'{self.menu_item.name}'

        )


# =====================================
# COMBO MEAL (COMPOSITE)
# =====================================

class ComboMeal(MenuComponent):

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

    description = models.TextField(

        blank=True,

        null=True

    )

    image = models.ImageField(

        upload_to='combo_meals/',

        blank=True,

        null=True

    )

    items = models.ManyToManyField(

        MenuItem,

        related_name='combo_meals'

    )

    discount_percent = models.DecimalField(

        max_digits=5,

        decimal_places=2,

        default=0

    )

    fixed_price = models.DecimalField(

        max_digits=10,

        decimal_places=2,

        blank=True,

        null=True

    )

    is_active = models.BooleanField(
        default=True
    )

    def get_total_price(self):

        if self.fixed_price is not None:

            return self.fixed_price

        total = sum(

            item.price

            for item in self.items.all()

        )

        discount = (

            total

            *

            self.discount_percent

            / 100

        )

        return total - discount

    @property
    def item_count(self):

        return self.items.count()

    def __str__(self):

        return self.name
