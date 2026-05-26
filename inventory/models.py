from django.db import models

from restaurants.models import (
    Restaurant,
    Branch
)

from decimal import Decimal


# =====================================
# PRODUCT
# =====================================

class Product(models.Model):

    UNIT_CHOICES = [

        ('kg', 'Kilogram'),

        ('g', 'Gram'),

        ('l', 'Liter'),

        ('ml', 'Milliliter'),

        ('pcs', 'Pieces'),

    ]

    restaurant = models.ForeignKey(

        Restaurant,

        on_delete=models.CASCADE,

        related_name='inventory_products',

        null=True,

        blank=True

    )

    branch = models.ForeignKey(

        Branch,

        on_delete=models.CASCADE,

        related_name='inventory_products',

        null=True,

        blank=True

    )

    name = models.CharField(
        max_length=255
    )

    quantity = models.FloatField(
        default=0
    )

    minimum_quantity = models.FloatField(
        default=5
    )

    unit = models.CharField(

        max_length=20,

        choices=UNIT_CHOICES,

        default='pcs'

    )

    cost_price = models.DecimalField(

        max_digits=10,

        decimal_places=2,

        default=0

    )

    barcode = models.CharField(

        max_length=255,

        blank=True,

        null=True

    )

    supplier_code = models.CharField(

        max_length=255,

        blank=True,

        null=True

    )

    expiry_tracking = models.BooleanField(
        default=False
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

    def is_low_stock(self):

        return (

            self.quantity <=

            self.minimum_quantity

        )

    @property
    def inventory_value(self):

        return (

            Decimal(str(self.quantity))

            *

            self.cost_price

        )

    def __str__(self):

        return self.name


# =====================================
# RECIPE INGREDIENT
# =====================================

class RecipeIngredient(models.Model):

    menu_item = models.ForeignKey(

        'menu.MenuItem',

        on_delete=models.CASCADE,

        related_name='recipe_items'

    )

    product = models.ForeignKey(

        Product,

        on_delete=models.CASCADE

    )

    quantity_required = models.FloatField(
        default=1
    )

    created_at = models.DateTimeField(

        auto_now_add=True,

        null=True,

        blank=True

    )

    @property
    def ingredient_cost(self):

        return (

            Decimal(str(self.quantity_required))

            *

            self.product.cost_price

        )

    def __str__(self):

        return (

            f'{self.menu_item.name}'

            f' -> '

            f'{self.product.name}'

        )


# =====================================
# SUPPLIER
# =====================================

class Supplier(models.Model):

    restaurant = models.ForeignKey(

        Restaurant,

        on_delete=models.CASCADE,

        related_name='suppliers',

        null=True,

        blank=True

    )

    branch = models.ForeignKey(

        Branch,

        on_delete=models.CASCADE,

        related_name='suppliers',

        null=True,

        blank=True

    )

    name = models.CharField(
        max_length=255
    )

    phone = models.CharField(

        max_length=50,

        blank=True,

        null=True

    )

    address = models.TextField(

        blank=True,

        null=True

    )

    email = models.EmailField(

        blank=True,

        null=True

    )

    created_at = models.DateTimeField(

        auto_now_add=True,

        null=True,

        blank=True

    )

    def __str__(self):

        return self.name


# =====================================
# PURCHASE
# =====================================

class Purchase(models.Model):

    STATUS_CHOICES = [

        ('draft', 'Draft'),

        ('received', 'Received'),

        ('returned', 'Returned'),

        ('cancelled', 'Cancelled'),

    ]

    restaurant = models.ForeignKey(

        Restaurant,

        on_delete=models.CASCADE,

        related_name='purchases',

        null=True,

        blank=True

    )

    branch = models.ForeignKey(

        Branch,

        on_delete=models.CASCADE,

        related_name='purchases',

        null=True,

        blank=True

    )

    supplier = models.ForeignKey(

        Supplier,

        on_delete=models.CASCADE,

        related_name='purchases'

    )

    invoice_number = models.CharField(

        max_length=100,

        unique=True

    )

    status = models.CharField(

        max_length=20,

        choices=STATUS_CHOICES,

        default='draft'

    )

    total_amount = models.DecimalField(

        max_digits=12,

        decimal_places=2,

        default=0

    )

    notes = models.TextField(

        blank=True,

        null=True

    )

    due_date = models.DateField(
        null=True,
        blank=True
    )

    returned_at = models.DateTimeField(
        null=True,
        blank=True
    )

    return_reason = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(

        auto_now_add=True,

        null=True,

        blank=True

    )

    def calculate_total(self):

        total = Decimal('0')

        for item in self.items.all():

            total += item.subtotal()

        return total


    def receive_products(self):

        if self.status == 'received':

            return

        for item in self.items.all():

            product = item.product

            before_qty = product.quantity

            product.quantity += item.quantity

            product.save()

            StockMovement.objects.create(

                product=product,

                movement_type='purchase',

                quantity=item.quantity,

                before_quantity=before_qty,

                after_quantity=product.quantity,

                note=(

                    f'Purchase '

                    f'{self.invoice_number}'

                )

            )

        self.status = 'received'

        self.save(
            update_fields=['status']
        )


    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        total = self.calculate_total()

        Purchase.objects.filter(
            id=self.id
        ).update(
            total_amount=total
        )

    def __str__(self):

        return self.invoice_number


# =====================================
# PURCHASE ITEM
# =====================================

class PurchaseItem(models.Model):

    purchase = models.ForeignKey(

        Purchase,

        on_delete=models.CASCADE,

        related_name='items'

    )

    product = models.ForeignKey(

        Product,

        on_delete=models.CASCADE

    )

    quantity = models.FloatField(
        default=1
    )

    cost_price = models.DecimalField(

        max_digits=10,

        decimal_places=2,

        default=0

    )

    created_at = models.DateTimeField(

        auto_now_add=True,

        null=True,

        blank=True

    )

    def subtotal(self):

        return (

            Decimal(str(self.quantity))

            *

            self.cost_price

        )

    def __str__(self):

        return (

            f'{self.purchase.invoice_number}'

            f' -> '

            f'{self.product.name}'

        )


# =====================================
# STOCK MOVEMENT
# =====================================

class StockMovement(models.Model):

    TYPE_CHOICES = [

        ('purchase', 'Purchase'),

        ('sale', 'Sale'),

        ('waste', 'Waste'),

        ('adjustment', 'Adjustment'),

        ('auto_deduction', 'Auto Deduction'),

    ]

    product = models.ForeignKey(

        Product,

        on_delete=models.CASCADE,

        related_name='movements'

    )

    movement_type = models.CharField(

        max_length=20,

        choices=TYPE_CHOICES

    )

    quantity = models.FloatField()

    before_quantity = models.FloatField(
        default=0
    )

    after_quantity = models.FloatField(
        default=0
    )

    note = models.TextField(

        blank=True,

        null=True

    )

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    def __str__(self):

        return (

            f'{self.product.name} '

            f'- '

            f'{self.movement_type}'

        )


# =====================================
# INVENTORY WASTE
# =====================================

class InventoryWaste(models.Model):

    product = models.ForeignKey(

        Product,

        on_delete=models.CASCADE,

        related_name='wastes'

    )

    quantity = models.FloatField()

    reason = models.TextField()

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    def save(self, *args, **kwargs):

        before_qty = self.product.quantity

        self.product.quantity -= self.quantity

        self.product.save()

        StockMovement.objects.create(

            product=self.product,

            movement_type='waste',

            quantity=self.quantity,

            before_quantity=before_qty,

            after_quantity=self.product.quantity,

            note=self.reason

        )

        super().save(*args, **kwargs)

    def __str__(self):

        return (

            f'Waste - '

            f'{self.product.name}'

        )


# =====================================
# INVENTORY CONSUMPTION
# =====================================

class InventoryConsumption(models.Model):

    order = models.ForeignKey(

        'orders.Order',

        on_delete=models.CASCADE,

        related_name='inventory_consumptions'

    )

    product = models.ForeignKey(

        Product,

        on_delete=models.CASCADE

    )

    quantity_used = models.FloatField()

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    def __str__(self):

        return (

            f'Order #{self.order.id} '

            f'- '

            f'{self.product.name}'

        )


# =====================================
# PRODUCT EXPIRY
# =====================================

class ProductExpiry(models.Model):

    product = models.ForeignKey(

        Product,

        on_delete=models.CASCADE,

        related_name='expiry_dates'

    )

    quantity = models.FloatField()

    expiry_date = models.DateField()

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    def __str__(self):

        return (

            f'{self.product.name} '

            f'- '

            f'{self.expiry_date}'

        )
