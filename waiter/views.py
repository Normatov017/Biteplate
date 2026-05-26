from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)
from django.db.models import Q
from django.utils import timezone

from orders.models import (
    Table,
    Order,
    OrderItem
)

from menu.models import (
    MenuItem
)

from permissionsapp.utils import (
    permission_required
)


# =====================================
# WAITER TABLES
# =====================================

@permission_required(
    'waiter',
    'view'
)
def waiter_tables(request):

    tables = Table.objects.filter(
        is_active=True
    ).order_by(
        'table_number'
    )

    context = {

        'tables': tables

    }

    return render(
        request,
        'waiter/tables.html',
        context
    )


# =====================================
# WAITER POS
# =====================================

@permission_required(
    'waiter',
    'view'
)
def waiter_pos(
    request,
    table_id
):

    table = get_object_or_404(
        Table,
        id=table_id
    )

    order = Order.objects.filter(
        table=table,
        status__in=[
            'pending',
            'preparing',
            'ready'
        ]
    ).first()

    if not order:

        order = Order.objects.create(
            table=table,
            status='pending',
            kitchen_status='waiting'
        )

        table.status = 'occupied'
        table.save()

    now_time = timezone.localtime().time()

    products = MenuItem.objects.filter(
        available=True
    ).filter(
        Q(available_from__isnull=True)
        | Q(available_from__lte=now_time)
    ).filter(
        Q(available_to__isnull=True)
        | Q(available_to__gte=now_time)
    ).order_by(
        'name'
    )

    total = 0

    for item in order.items.all():

        total += item.get_total()

    context = {

        'table': table,

        'order': order,

        'products': products,

        'menu_items': products,

        'total': total,

    }

    return render(
        request,
        'waiter/pos.html',
        context
    )


# =====================================
# ADD ITEM
# =====================================

@permission_required(
    'waiter',
    'edit'
)
def waiter_add_item(
    request,
    order_id,
    item_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    menu_item = get_object_or_404(
        MenuItem,
        id=item_id
    )

    order_item = OrderItem.objects.filter(
        order=order,
        menu_item=menu_item,
        kitchen_status__in=[
            'draft',
            'waiting'
        ]
    ).first()

    if order_item:

        order_item.quantity += 1

        order_item.save()

    else:

        OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=1,
            kitchen_status='draft'
        )

    return redirect(
        'waiter_pos',
        table_id=order.table.id
    )


# =====================================
# REMOVE ITEM
# =====================================

@permission_required(
    'waiter',
    'edit'
)
def remove_order_item(
    request,
    item_id
):

    item = get_object_or_404(
        OrderItem,
        id=item_id
    )

    table_id = item.order.table.id

    item.delete()

    return redirect(
        'waiter_pos',
        table_id=table_id
    )


# =====================================
# SEND TO KITCHEN
# =====================================

@permission_required(
    'orders',
    'edit'
)
def send_to_kitchen(
    request,
    order_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    order.status = 'pending'

    order.kitchen_status = 'waiting'

    order.save()

    OrderItem.objects.filter(
        order=order,
        kitchen_status='draft'
    ).update(
        kitchen_status='waiting',
        sent_to_kitchen_at=timezone.now()
    )

    next_url = request.GET.get('next') or request.POST.get('next')

    if next_url:

        return redirect(next_url)

    return redirect(
        'waiter_pos',
        table_id=order.table.id
    )


# =====================================
# CALL WAITER
# =====================================

@permission_required(
    'waiter',
    'view'
)
def call_waiter(
    request,
    table_id
):

    table = get_object_or_404(
        Table,
        id=table_id
    )

    return redirect(
        'waiter_pos',
        table_id=table.id
    )
