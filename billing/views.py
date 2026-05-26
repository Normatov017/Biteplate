from decimal import Decimal
from decimal import InvalidOperation

from django.contrib import messages
from django.db.models import Sum

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render
)

from billing.models import Payment

from inventory.services import InventoryService

from orders.models import (
    Order,
    OrderItem
)


PAYMENT_METHODS = [

    ('cash', 'Cash'),

    ('card', 'Card'),

    ('click', 'Click'),

    ('payme', 'Payme'),

]


# =========================
# TOTAL HELPERS
# =========================

def get_order_total(order):

    total = Decimal('0')

    for item in order.items.all():

        total += item.get_total()

    return total


def get_paid_total(order):

    paid_total = order.payments.filter(

        status='paid'

    ).aggregate(

        total=Sum('amount')

    )['total']

    return paid_total or Decimal('0')


# =========================
# CLOSE PAID ORDER
# =========================

def close_paid_order(

    order,

    payment_method

):

    if order.is_paid:

        return

    InventoryService.deduct_order_inventory(order)

    order.payment_method = payment_method

    order.is_paid = True

    order.status = 'completed'

    order.kitchen_status = 'served'

    order.save()

    table = order.table

    table.status = 'free' if table.table_number == 0 else 'cleaning'

    table.save()


# =========================
# BILL PAGE
# =========================

def generate_bill(

    request,

    order_id

):

    order = get_object_or_404(

        Order,

        id=order_id

    )

    total = get_order_total(order)

    paid_total = get_paid_total(order)

    remaining_total = total - paid_total

    available_orders = Order.objects.exclude(

        id=order.id

    ).exclude(

        status__in=[
            'served',
            'cancelled'
        ]

    )

    context = {

        'order': order,

        'total': total,

        'paid_total': paid_total,

        'remaining_total': remaining_total,

        'payment_methods': PAYMENT_METHODS,

        'available_orders': available_orders,

    }

    return render(

        request,

        'bill.html',

        context

    )


# =========================
# SINGLE PAYMENT
# =========================

def complete_payment(

    request,

    order_id,

    method

):

    order = get_object_or_404(

        Order,

        id=order_id

    )

    total = get_order_total(order)

    paid_total = get_paid_total(order)

    remaining_total = total - paid_total

    if remaining_total <= 0:

        messages.info(

            request,

            'This order is already fully paid.'

        )

        return redirect(

            'generate_bill',

            order_id=order.id

        )

    Payment.objects.create(

        order=order,

        amount=remaining_total,

        method=method,

        status='paid'

    )

    close_paid_order(

        order,

        method

    )

    messages.success(

        request,

        f'Payment completed with {method.upper()}.'

    )

    return redirect(

        'dashboard'

    )


# =========================
# SPLIT PAYMENT
# =========================

def split_payment(

    request,

    order_id

):

    order = get_object_or_404(

        Order,

        id=order_id

    )

    if request.method != 'POST':

        return redirect(

            'generate_bill',

            order_id=order.id

        )

    total = get_order_total(order)

    paid_total = get_paid_total(order)

    remaining_total = total - paid_total

    if remaining_total <= 0:

        messages.info(

            request,

            'This order is already fully paid.'

        )

        return redirect(

            'generate_bill',

            order_id=order.id

        )

    split_rows = []

    split_total = Decimal('0')

    for method, label in PAYMENT_METHODS:

        raw_amount = request.POST.get(

            method,

            ''

        ).strip()

        if not raw_amount:

            continue

        try:

            amount = Decimal(raw_amount)

        except InvalidOperation:

            messages.error(

                request,

                f'{label} amount is not valid.'

            )

            return redirect(

                'generate_bill',

                order_id=order.id

            )

        if amount < 0:

            messages.error(

                request,

                'Split payment amounts cannot be negative.'

            )

            return redirect(

                'generate_bill',

                order_id=order.id

            )

        if amount == 0:

            continue

        split_rows.append(

            (method, amount)

        )

        split_total += amount

    if not split_rows:

        messages.error(

            request,

            'Enter at least one split payment amount.'

        )

        return redirect(

            'generate_bill',

            order_id=order.id

        )

    if split_total != remaining_total:

        messages.error(

            request,

            f'Split total must equal remaining amount: ${remaining_total}.'

        )

        return redirect(

            'generate_bill',

            order_id=order.id

        )

    for method, amount in split_rows:

        Payment.objects.create(

            order=order,

            amount=amount,

            method=method,

            status='paid'

        )

    close_paid_order(

        order,

        'split'

        if len(split_rows) > 1

        else split_rows[0][0]

    )

    messages.success(

        request,

        'Split payment completed.'

    )

    return redirect(

        'dashboard'

    )


# =========================
# MERGE ORDERS
# =========================

def merge_orders(

    request,

    source_order_id,

    target_order_id

):

    source_order = get_object_or_404(

        Order,

        id=source_order_id

    )

    target_order = get_object_or_404(

        Order,

        id=target_order_id

    )

    if source_order.id == target_order.id:

        messages.error(

            request,

            'Cannot merge same order.'

        )

        return redirect(

            'generate_bill',

            order_id=source_order.id

        )

    for item in source_order.items.all():

        existing_item = target_order.items.filter(

            menu_item=item.menu_item

        ).first()

        if existing_item:

            existing_item.quantity += item.quantity

            existing_item.save()

            item.delete()

        else:

            item.order = target_order

            item.save()

    source_order.is_merged = True

    source_order.merged_into = target_order

    source_order.status = 'cancelled'

    source_order.save()

    messages.success(

        request,

        (

            f'Order #{source_order.id} '

            f'merged into '

            f'Order #{target_order.id}'

        )

    )

    return redirect(

        'generate_bill',

        order_id=target_order.id

    )


# =========================
# TRANSFER ITEM
# =========================

def transfer_item(

    request,

    item_id,

    target_order_id

):

    order_item = get_object_or_404(

        OrderItem,

        id=item_id

    )

    target_order = get_object_or_404(

        Order,

        id=target_order_id

    )

    source_order = order_item.order

    existing_item = target_order.items.filter(

        menu_item=order_item.menu_item

    ).first()

    if existing_item:

        existing_item.quantity += order_item.quantity

        existing_item.save()

        order_item.delete()

    else:

        order_item.order = target_order

        order_item.save()

    messages.success(

        request,

        (

            f'Item transferred '

            f'to Order '

            f'#{target_order.id}'

        )

    )

    return redirect(

        'generate_bill',

        order_id=source_order.id

    )
