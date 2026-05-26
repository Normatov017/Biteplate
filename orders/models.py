from django.db import models

from restaurants.models import Restaurant
from restaurants.models import Branch

from simple_history.models import HistoricalRecords


# =========================
# TABLE MODEL
# =========================

class Table(models.Model):

    STATUS_CHOICES = [

        ('free', 'Free'),
        ('reserved', 'Reserved'),
        ('occupied', 'Occupied'),
        ('awaiting_bill', 'Awaiting Bill'),
        ('cleaning', 'Cleaning'),

    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='tables',
        null=True,
        blank=True
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='tables',
        null=True,
        blank=True
    )

    table_number = models.IntegerField()

    seats = models.IntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='free'
    )

    assigned_waiter = models.CharField(
        max_length=100,
        default='Ali'
    )

    is_active = models.BooleanField(
        default=True
    )

    floor_area = models.CharField(
        max_length=80,
        default='Main Floor'
    )

    pos_x = models.IntegerField(
        default=120
    )

    pos_y = models.IntegerField(
        default=120
    )

    pos_width = models.IntegerField(
        default=120
    )

    pos_height = models.IntegerField(
        default=90
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    history = HistoricalRecords()

    def __str__(self):

        return f'Table {self.table_number}'


# =========================
# ORDER MODEL
# =========================

class Order(models.Model):

    STATUS_CHOICES = [

        ('pending', 'Pending'),

        ('held', 'Held'),

        ('preparing', 'Preparing'),

        ('ready', 'Ready'),

        ('served', 'Served'),

        ('completed', 'Completed'),

        ('cancelled', 'Cancelled'),

    ]


    KITCHEN_STATUS = [

        ('waiting', 'Waiting'),

        ('preparing', 'Preparing'),

        ('ready', 'Ready'),

        ('served', 'Served'),

        ('cancelled', 'Cancelled'),

    ]


    PAYMENT_CHOICES = [

        ('cash', 'Cash'),

        ('card', 'Card'),

        ('click', 'Click'),

        ('payme', 'Payme'),

        ('split', 'Split'),

    ]


    PRIORITY_FLAG_CHOICES = [

        ('normal', 'Normal'),

        ('rush', 'Rush'),

        ('vip', 'VIP'),

    ]


    ORDER_TYPE_CHOICES = [

        ('dine_in', 'Dine In'),

        ('takeaway', 'Takeaway'),

        ('delivery', 'Delivery'),

    ]


    pricing_type = models.CharField(
        max_length=50,
        default='standard'
    )

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='orders',
        null=True,
        blank=True
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='orders',
        null=True,
        blank=True
    )

    waiter = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        related_name='served_orders',
        null=True,
        blank=True
    )

    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPE_CHOICES,
        default='dine_in'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    kitchen_status = models.CharField(
        max_length=20,
        choices=KITCHEN_STATUS,
        default='waiting'
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        blank=True,
        null=True
    )

    source_order = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='split_orders',
        blank=True,
        null=True
    )

    merged_into = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='merged_orders',
        blank=True,
        null=True
    )

    priority_flag = models.CharField(
        max_length=20,
        choices=PRIORITY_FLAG_CHOICES,
        default='normal'
    )

    delivery_address = models.TextField(
        blank=True,
        null=True
    )

    printer_route = models.CharField(
        max_length=50,
        default='kitchen'
    )

    void_reason = models.TextField(
        blank=True,
        null=True
    )

    refund_reason = models.TextField(
        blank=True,
        null=True
    )

    held_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_paid = models.BooleanField(
        default=False
    )

    priority = models.IntegerField(
        default=1
    )

    estimated_time = models.IntegerField(
        default=15
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    service_charge_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    customer_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    customer_phone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    guest_count = models.IntegerField(
        default=1
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True
    )

    ready_at = models.DateTimeField(
        null=True,
        blank=True
    )

    completed_at = models.DateTimeField(
        null=True,
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


    # =========================
    # AUTO PRIORITY
    # =========================

    def auto_priority(self):

        item_count = self.items.count()

        if self.priority_flag == 'rush':

            return 10

        if self.priority_flag == 'vip':

            return 8

        if item_count >= 8:

            return 5

        elif item_count >= 5:

            return 4

        elif item_count >= 3:

            return 3

        return 1


    # =========================
    # CALCULATE TOTAL
    # =========================

    @property
    def get_total(self):

        total = 0

        for item in self.items.all():

            total += item.get_total()

        return total


    def calculate_total(self):

        total = 0

        for item in self.items.all():

            total += item.get_total()

        discount = self.discount_amount or 0

        discounted_total = max(
            total - discount,
            0
        )

        service_charge = (
            discounted_total *
            self.service_charge_percent /
            100
        )

        gratuity = 0

        if self.guest_count >= 8:

            gratuity = discounted_total * 12 / 100

        return discounted_total + service_charge + gratuity


    @property
    def subtotal_amount(self):

        total = 0

        for item in self.items.all():

            total += item.get_total()

        return total


    @property
    def service_charge_amount(self):

        discounted_total = max(
            self.subtotal_amount - self.discount_amount,
            0
        )

        return (
            discounted_total *
            self.service_charge_percent /
            100
        )


    @property
    def gratuity_amount(self):

        if self.guest_count < 8:

            return 0

        discounted_total = max(
            self.subtotal_amount - self.discount_amount,
            0
        )

        return discounted_total * 12 / 100


    # =========================
    # SAVE
    # =========================

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        self.total_amount = self.calculate_total()

        self.priority = self.auto_priority()

        super().save(

            update_fields=[
                'total_amount',
                'priority'
            ]

        )


    def __str__(self):

        return f'Order #{self.id}'


# =========================
# ORDER ITEM
# =========================

class OrderItem(models.Model):

    COURSE_CHOICES = [

        ('starter', 'Starter'),

        ('main', 'Main'),

        ('dessert', 'Dessert'),

        ('drinks', 'Drinks'),

    ]

    KITCHEN_STATUS_CHOICES = [

        ('draft', 'Draft'),

        ('waiting', 'Waiting'),

        ('preparing', 'Preparing'),

        ('ready', 'Ready'),

        ('served', 'Served'),

        ('cancelled', 'Cancelled'),

    ]

    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )

    menu_item = models.ForeignKey(
        'menu.MenuItem',
        on_delete=models.CASCADE
    )

    variant = models.ForeignKey(
        'menu.ProductVariant',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    quantity = models.IntegerField(
        default=1
    )

    course = models.CharField(
        max_length=20,
        choices=COURSE_CHOICES,
        default='main'
    )

    guest_name = models.CharField(
        max_length=120,
        blank=True,
        null=True
    )

    notes = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    kitchen_status = models.CharField(
        max_length=20,
        choices=KITCHEN_STATUS_CHOICES,
        default='draft'
    )

    sent_to_kitchen_at = models.DateTimeField(
        null=True,
        blank=True
    )

    refunded = models.BooleanField(
        default=False
    )

    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    history = HistoricalRecords()


    def get_total(self):

        if self.refunded:

            return 0

        total = self.menu_item.price

        if self.variant:

            total += self.variant.extra_price

        total *= self.quantity

        for modifier in self.modifiers.all():

            total += (

                modifier.extra_price *
                self.quantity

            )

        return total


    def __str__(self):

        return (

            f'{self.menu_item.name}'
            f' x '
            f'{self.quantity}'

        )


# =========================
# ORDER ITEM MODIFIER
# =========================

class OrderItemModifier(models.Model):

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='modifiers'
    )

    modifier_option = models.ForeignKey(
        'menu.ModifierOption',
        on_delete=models.CASCADE
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

    history = HistoricalRecords()


    def save(self, *args, **kwargs):

        self.extra_price = (

            self.modifier_option.extra_price

        )

        super().save(*args, **kwargs)


    def __str__(self):

        return (

            f'{self.order_item.menu_item.name}'
            f' -> '
            f'{self.modifier_option.name}'

        )
