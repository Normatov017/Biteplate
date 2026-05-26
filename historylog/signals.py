from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User
from billing.models import Payment
from inventory.models import Product, Purchase
from menu.models import MenuItem
from orders.models import Order, OrderItem, Table

from .audit import get_current_user
from .models import ActionAuditLog


TRACKED_MODELS = (
    Order,
    OrderItem,
    Payment,
    MenuItem,
    Product,
    Purchase,
    Table,
    User,
)


@receiver(post_save)
def create_action_audit(sender, instance, created, **kwargs):

    if sender not in TRACKED_MODELS:

        return

    ActionAuditLog.objects.create(
        user=get_current_user(),
        model_name=sender.__name__,
        object_id=str(instance.pk),
        action='create' if created else 'update',
        summary=str(instance)
    )
