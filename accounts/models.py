from django.db import models

from django.contrib.auth.models import (
    AbstractUser
)

from restaurants.models import (
    Restaurant,
    Branch
)


# =====================================
# USER MODEL
# =====================================

class User(AbstractUser):

    STATUS_CHOICES = [

        ('active', 'Active'),

        ('inactive', 'Inactive'),

        ('vacation', 'Vacation'),

        ('blocked', 'Blocked'),

    ]

    restaurant = models.ForeignKey(

        Restaurant,

        on_delete=models.CASCADE,

        related_name='users',

        null=True,

        blank=True

    )

    branch = models.ForeignKey(

        Branch,

        on_delete=models.CASCADE,

        related_name='users',

        null=True,

        blank=True

    )

    role = models.ForeignKey(

        'permissionsapp.Role',

        on_delete=models.SET_NULL,

        related_name='users',

        null=True,

        blank=True,


    )

    phone = models.CharField(

        max_length=50,

        blank=True,

        null=True

    )

    avatar = models.ImageField(

        upload_to='avatars/',

        blank=True,

        null=True

    )

    salary = models.DecimalField(

        max_digits=12,

        decimal_places=2,

        default=0

    )

    hire_date = models.DateField(

        null=True,

        blank=True

    )

    birth_date = models.DateField(

        null=True,

        blank=True

    )

    address = models.TextField(

        blank=True,

        null=True

    )

    emergency_contact = models.CharField(

        max_length=255,

        blank=True,

        null=True

    )

    employee_id = models.CharField(

        max_length=100,

        blank=True,

        null=True,

        unique=True

    )

    waiter_pin = models.CharField(

        max_length=12,

        blank=True,

        null=True,

        unique=True

    )

    is_online = models.BooleanField(
        default=False
    )

    last_activity = models.DateTimeField(

        null=True,

        blank=True

    )

    status = models.CharField(

        max_length=20,

        choices=STATUS_CHOICES,

        default='active'

    )

    notes = models.TextField(

        blank=True,

        null=True

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


    # =====================================
    # USER FULL NAME
    # =====================================

    @property
    def full_name(self):

        return (

            f'{self.first_name} '

            f'{self.last_name}'

        ).strip()


    # =====================================
    # ROLE NAME
    # =====================================

    @property
    def role_name(self):

        if self.role:

            return self.role.name

        return 'No Role'


    # =====================================
    # IS MANAGER
    # =====================================

    @property
    def is_manager(self):

        if not self.role:

            return False

        return (

            self.role.name.lower()

            == 'manager'

        )


    # =====================================
    # IS WAITER
    # =====================================

    @property
    def is_waiter(self):

        if not self.role:

            return False

        return (

            self.role.name.lower()

            == 'waiter'

        )


    # =====================================
    # IS CASHIER
    # =====================================

    @property
    def is_cashier(self):

        if not self.role:

            return False

        return (

            self.role.name.lower()

            == 'cashier'

        )


    # =====================================
    # IS KITCHEN
    # =====================================

    @property
    def is_kitchen(self):

        if not self.role:

            return False

        return (

            self.role.name.lower()

            == 'kitchen'

        )


    # =====================================
    # IS OWNER
    # =====================================

    @property
    def is_owner(self):

        if not self.role:

            return False

        return (

            self.role.name.lower()

            == 'owner'

        )


    # =====================================
    # SAVE
    # =====================================

    def save(self, *args, **kwargs):

        if self.username:

            self.username = (

                self.username.lower()

            )

        if self.email:

            self.email = (

                self.email.lower()

            )

        super().save(*args, **kwargs)


    # =====================================
    # STRING
    # =====================================

    def __str__(self):

        return (

            f'{self.username} '

            f'({self.role_name})'

        )
