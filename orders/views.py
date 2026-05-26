from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from decimal import Decimal
from decimal import InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    Table,
    Order,
    OrderItem,
    OrderItemModifier
)

from menu.models import (
    ComboMeal,
    MenuItem,
    ModifierOption
)

from realtime.utils import (
    send_order_update
)

from permissionsapp.utils import (
    permission_required
)

from settingsapp.models import (
    SystemSettings
)


ACTIVE_ORDER_STATUSES = [
    'pending',
    'held',
    'preparing',
    'ready',
    'served',
]


def _open_orders():

    return Order.objects.filter(
        status__in=ACTIVE_ORDER_STATUSES,
        merged_into__isnull=True
    ).order_by(
        '-created_at'
    )


def _refresh_table_status(table):

    has_open_order = _open_orders().filter(
        table=table
    ).exists()

    table.status = (
        'occupied'
        if has_open_order
        else 'free'
    )

    table.save(
        update_fields=['status']
    )


def _copy_item_to_order(item, order, quantity=None):

    cloned_item = OrderItem.objects.create(
        order=order,
        menu_item=item.menu_item,
        variant=item.variant,
        quantity=quantity or item.quantity,
        course=item.course,
        guest_name=item.guest_name,
        notes=item.notes
    )

    for modifier in item.modifiers.all():

        OrderItemModifier.objects.create(
            order_item=cloned_item,
            modifier_option=modifier.modifier_option
        )

    return cloned_item


def _decimal_from_post(request, key, default='0'):

    try:

        return Decimal(
            request.POST.get(
                key,
                default
            ) or default
        )

    except InvalidOperation:

        return Decimal(default)


# =====================================
# TABLES DASHBOARD
# =====================================

@permission_required(
    'tables',
    'view'
)
def table_list(request):

    tables = Table.objects.filter(
        is_active=True
    ).exclude(
        table_number=0
    ).prefetch_related(
        'orders'
    ).order_by(
        'table_number'
    )

    active_orders = _open_orders().select_related(
        'table'
    ).prefetch_related(
        'items'
    )

    order_by_table = {}

    for order in active_orders:

        if order.table_id not in order_by_table:

            order_by_table[order.table_id] = order

    for table in tables:

        table.active_order = order_by_table.get(
            table.id
        )

    visible_tables = Table.objects.exclude(
        table_number=0
    )

    occupied_tables = visible_tables.filter(
        status='occupied'
    ).count()

    free_tables = visible_tables.filter(
        status='free'
    ).count()

    reserved_tables = visible_tables.filter(
        status='reserved'
    ).count()

    cleaning_tables = visible_tables.filter(
        status='cleaning'
    ).count()

    context = {

        'tables': tables,

        'occupied_tables': occupied_tables,

        'free_tables': free_tables,

        'reserved_tables': reserved_tables,

        'cleaning_tables': cleaning_tables,

        'held_orders': Order.objects.filter(
            status='held'
        ).count(),

    }

    return render(
        request,
        'tables.html',
        context
    )


# =====================================
# CREATE ORDER
# =====================================

@permission_required(
    'orders',
    'create'
)
def create_order(
    request,
    table_id
):

    table = get_object_or_404(
        Table,
        id=table_id
    )

    existing_order = _open_orders().filter(
        table=table,
    ).first()

    if existing_order:

        return redirect(
            'order_detail',
            order_id=existing_order.id
        )

    order = Order.objects.create(
        table=table,
        order_type=request.POST.get(
            'order_type',
            'dine_in'
        ),
        status='pending',
        kitchen_status='waiting',
        printer_route=request.POST.get(
            'printer_route',
            'kitchen'
        )
    )

    table.status = 'occupied'
    table.save()

    try:

        send_order_update(
            {
                'type': 'new_order',
                'order_id': order.id,
                'table': table.table_number,
                'status': 'waiting',
                'message': (
                    f'New Order #{order.id} '
                    f'for Table '
                    f'{table.table_number}'
                )
            }
        )

    except Exception as e:

        print(
            'Realtime Error:',
            str(e)
        )

    return redirect(
        'order_detail',
        order_id=order.id
    )


# =====================================
# ORDER DETAIL
# =====================================

@permission_required(
    'orders',
    'view'
)
def order_detail(
    request,
    order_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    now_time = timezone.localtime().time()

    menu_items = MenuItem.objects.filter(
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

    combo_meals = ComboMeal.objects.filter(
        is_active=True
    ).prefetch_related(
        'items'
    ).order_by(
        'name'
    )

    modifier_options = ModifierOption.objects.select_related(
        'group'
    ).order_by(
        'group__name',
        'name'
    )

    tables = Table.objects.filter(
        is_active=True
    ).exclude(
        id=order.table_id
    ).order_by(
        'table_number'
    )

    open_orders = _open_orders().exclude(
        id=order.id
    ).select_related(
        'table'
    ).order_by(
        'table__table_number'
    )

    total = 0

    for item in order.items.all():

        total += item.get_total()

    context = {

        'order': order,

        'menu_items': menu_items,

        'combo_meals': combo_meals,

        'modifier_options': modifier_options,

        'tables': tables,

        'all_tables': Table.objects.filter(
            is_active=True
        ).order_by(
            'table_number'
        ),

        'open_orders': open_orders,

        'order_items': order.items.select_related(
            'menu_item'
        ).prefetch_related(
            'modifiers__modifier_option'
        ),

        'total': total,

        'subtotal': order.subtotal_amount,

        'service_charge': order.service_charge_amount,

        'system_settings': SystemSettings.objects.first(),

    }

    return render(
        request,
        'order_detail.html',
        context
    )


# =====================================
# ADD ITEM TO ORDER
# =====================================

@permission_required(
    'orders',
    'edit'
)
def add_to_order(
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

    notes = request.POST.get(
        'notes',
        ''
    ).strip()

    course = request.POST.get(
        'course',
        'main'
    )

    modifier_ids = request.POST.getlist(
        'modifiers'
    )

    order_item = OrderItem.objects.filter(
        order=order,
        menu_item=menu_item,
        notes=notes or None,
        course=course,
        kitchen_status__in=[
            'draft',
            'waiting'
        ]
    ).first()

    created = order_item is None

    if created:

        order_item = OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            notes=notes or None,
            course=course,
            quantity=1
        )

    if not created:

        order_item.quantity += 1
        order_item.save()

    for modifier_option in ModifierOption.objects.filter(
        id__in=modifier_ids
    ):

        OrderItemModifier.objects.get_or_create(
            order_item=order_item,
            modifier_option=modifier_option
        )

    order.total_amount = order.calculate_total()

    if request.GET.get('send') == '1':

        order_item.kitchen_status = 'waiting'
        order_item.sent_to_kitchen_at = timezone.now()
        order_item.save(
            update_fields=[
                'kitchen_status',
                'sent_to_kitchen_at'
            ]
        )
        order.status = 'pending'
        order.kitchen_status = 'waiting'

    order.save()

    try:

        send_order_update(
            {
                'type': 'item_added',
                'order_id': order.id,
                'table': order.table.table_number,
                'item': menu_item.name,
                'message': (
                    f'{menu_item.name} '
                    f'added to '
                    f'Order #{order.id}'
                )
            }
        )

    except Exception as e:

        print(
            'Realtime Error:',
            str(e)
        )

    if request.GET.get('send') == '1':

        messages.success(
            request,
            f'{menu_item.name} kitchen ga yuborildi.'
        )

        return redirect(
            'order_detail',
            order_id=order.id
        )

    return redirect(
        'order_detail',
        order_id=order.id
    )


# =====================================
# ADD COMBO TO ORDER
# =====================================

@permission_required(
    'orders',
    'edit'
)
def add_combo_to_order(
    request,
    order_id,
    combo_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    combo = get_object_or_404(
        ComboMeal,
        id=combo_id,
        is_active=True
    )

    for menu_item in combo.items.all():

        OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=1,
            kitchen_status='waiting'
            if request.GET.get('send') == '1'
            else 'draft',
            sent_to_kitchen_at=timezone.now()
            if request.GET.get('send') == '1'
            else None,
            course=menu_item.category
            if menu_item.category in [
                'starter',
                'dessert'
            ]
            else 'main',
            notes=(
                f'Combo: {combo.name} '
                f'({combo.discount_percent}% discount)'
            )
        )

    order.notes = (
        (order.notes or '')
        + f'\nCombo added: {combo.name}. '
        + f'Bundle price target: {combo.get_total_price()}.'
    ).strip()

    order.total_amount = order.calculate_total()

    if request.GET.get('send') == '1':

        order.status = 'pending'
        order.kitchen_status = 'waiting'

    order.save()

    messages.success(
        request,
        f'{combo.name} combo added.'
    )

    return redirect(
        'order_detail',
        order_id=order.id
    )


# =====================================
# REMOVE ITEM
# =====================================

@permission_required(
    'orders',
    'edit'
)
def remove_item(
    request,
    item_id
):

    item = get_object_or_404(
        OrderItem,
        id=item_id
    )

    order_id = item.order.id

    item.delete()

    return redirect(
        'order_detail',
        order_id=order_id
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

    order.items.filter(
        kitchen_status='draft'
    ).update(
        kitchen_status='waiting',
        sent_to_kitchen_at=timezone.now()
    )

    order.save()

    try:

        send_order_update(
            {
                'type': 'kitchen_update',
                'order_id': order.id,
                'table': order.table.table_number,
                'status': 'waiting',
                'message': (
                    f'Order #{order.id} '
                    f'sent to kitchen'
                )
            }
        )

    except Exception as e:

        print(
            'Realtime Error:',
            str(e)
        )

    return redirect(
        'kitchen_dashboard'
    )


# =====================================
# UPDATE ORDER WORKFLOW
# =====================================

@permission_required(
    'orders',
    'edit'
)
def update_order_workflow(
    request,
    order_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    if request.method == 'POST':

        requested_order_type = request.POST.get(
            'order_type',
            order.order_type
        )

        order.order_type = (
            requested_order_type
            if requested_order_type in ['dine_in']
            else 'dine_in'
        )

        order.priority_flag = request.POST.get(
            'priority_flag',
            order.priority_flag
        )

        order.printer_route = request.POST.get(
            'printer_route',
            order.printer_route
        )

        if request.POST.get('payment_method'):

            order.payment_method = request.POST.get(
                'payment_method'
            )

        if 'discount_amount' in request.POST:

            order.discount_amount = max(
                _decimal_from_post(
                    request,
                    'discount_amount'
                ),
                Decimal('0')
            )

        if 'service_charge_percent' in request.POST:

            order.service_charge_percent = max(
                _decimal_from_post(
                    request,
                    'service_charge_percent'
                ),
                Decimal('0')
            )

        order.save()

        messages.success(
            request,
            'Order workflow updated.'
        )

    return redirect(
        'order_detail',
        order_id=order.id
    )


# =====================================
# ITEM QUICK QUANTITY
# =====================================

@permission_required(
    'orders',
    'edit'
)
def adjust_order_item_quantity(
    request,
    item_id,
    action
):

    item = get_object_or_404(
        OrderItem,
        id=item_id
    )

    if action == 'increase':

        item.quantity += 1
        item.save()

    elif action == 'decrease':

        if item.quantity <= 1:

            item.delete()

        else:

            item.quantity -= 1
            item.save()

    item.order.save()

    return redirect(
        'order_detail',
        order_id=item.order.id
    )


# =====================================
# UPDATE ORDER ITEM
# =====================================

@permission_required(
    'orders',
    'edit'
)
def update_order_item(
    request,
    item_id
):

    item = get_object_or_404(
        OrderItem,
        id=item_id
    )

    if request.method == 'POST':

        item.quantity = max(
            1,
            int(
                request.POST.get(
                    'quantity',
                    item.quantity
                )
            )
        )

        item.course = request.POST.get(
            'course',
            item.course
        )

        item.notes = request.POST.get(
            'notes',
            ''
        ).strip() or None

        item.save()

        item.modifiers.all().delete()

        for modifier_option in ModifierOption.objects.filter(
            id__in=request.POST.getlist('modifiers')
        ):

            OrderItemModifier.objects.create(
                order_item=item,
                modifier_option=modifier_option
            )

        item.order.save()

        messages.success(
            request,
            'Item modifiers and notes updated.'
        )

    return redirect(
        'order_detail',
        order_id=item.order.id
    )


# =====================================
# HOLD / RECALL ORDER
# =====================================

@permission_required(
    'orders',
    'edit'
)
def hold_order(
    request,
    order_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    order.status = 'held'
    order.kitchen_status = 'waiting'
    order.held_at = timezone.now()
    order.save()

    messages.success(
        request,
        f'Order #{order.id} held.'
    )

    return redirect(
        'tables'
    )


@permission_required(
    'orders',
    'edit'
)
def recall_order(
    request,
    order_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    order.status = 'pending'
    order.held_at = None
    order.save()

    messages.success(
        request,
        f'Order #{order.id} recalled.'
    )

    return redirect(
        'order_detail',
        order_id=order.id
    )


# =====================================
# TRANSFER TABLE
# =====================================

@permission_required(
    'orders',
    'edit'
)
def transfer_order(
    request,
    order_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    if request.method == 'POST':

        target_table = get_object_or_404(
            Table,
            id=request.POST.get('target_table')
        )

        old_table = order.table
        order.table = target_table
        order.save()

        target_table.status = 'occupied'
        target_table.save(
            update_fields=['status']
        )

        _refresh_table_status(old_table)

        messages.success(
            request,
            (
                f'Order #{order.id} transferred '
                f'to Table {target_table.table_number}.'
            )
        )

    return redirect(
        'order_detail',
        order_id=order.id
    )


# =====================================
# MERGE ORDERS
# =====================================

@permission_required(
    'orders',
    'edit'
)
def merge_orders(
    request,
    order_id
):

    target_order = get_object_or_404(
        Order,
        id=order_id
    )

    if request.method == 'POST':

        source_order = get_object_or_404(
            Order,
            id=request.POST.get('source_order')
        )

        if source_order.id != target_order.id:

            with transaction.atomic():

                source_table = source_order.table

                for item in source_order.items.all():

                    item.order = target_order
                    item.save(
                        update_fields=['order']
                    )

                source_order.status = 'completed'
                source_order.merged_into = target_order
                source_order.notes = (
                    (source_order.notes or '')
                    + f'\nMerged into Order #{target_order.id}.'
                ).strip()
                source_order.save()

                target_order.notes = (
                    (target_order.notes or '')
                    + f'\nMerged Order #{source_order.id}.'
                ).strip()
                target_order.save()

                _refresh_table_status(source_table)
                target_order.table.status = 'occupied'
                target_order.table.save(
                    update_fields=['status']
                )

            messages.success(
                request,
                (
                    f'Order #{source_order.id} merged '
                    f'into #{target_order.id}.'
                )
            )

    return redirect(
        'order_detail',
        order_id=target_order.id
    )


# =====================================
# SPLIT ORDER
# =====================================

@permission_required(
    'orders',
    'edit'
)
def split_order(
    request,
    order_id
):

    source_order = get_object_or_404(
        Order,
        id=order_id
    )

    if request.method == 'POST':

        target_table = get_object_or_404(
            Table,
            id=request.POST.get('target_table')
        )

        with transaction.atomic():

            new_order = Order.objects.create(
                table=target_table,
                order_type=source_order.order_type,
                status='pending',
                kitchen_status='waiting',
                source_order=source_order,
                printer_route=source_order.printer_route
            )

            for item in source_order.items.all():

                quantity = int(
                    request.POST.get(
                        f'item_{item.id}',
                        0
                    ) or 0
                )

                if quantity <= 0:

                    continue

                quantity = min(
                    quantity,
                    item.quantity
                )

                _copy_item_to_order(
                    item,
                    new_order,
                    quantity=quantity
                )

                if quantity == item.quantity:

                    item.delete()

                else:

                    item.quantity -= quantity
                    item.save()

            new_order.save()
            source_order.save()

            target_table.status = 'occupied'
            target_table.save(
                update_fields=['status']
            )

        messages.success(
            request,
            f'Order #{source_order.id} split into #{new_order.id}.'
        )

    return redirect(
        'order_detail',
        order_id=source_order.id
    )


# =====================================
# REPEAT LAST ORDER
# =====================================

@permission_required(
    'orders',
    'edit'
)
def repeat_last_order(
    request,
    table_id
):

    table = get_object_or_404(
        Table,
        id=table_id
    )

    previous_order = Order.objects.filter(
        table=table,
        status__in=[
            'completed',
            'served',
            'cancelled'
        ]
    ).order_by(
        '-created_at'
    ).first()

    if not previous_order:

        messages.warning(
            request,
            'No previous order found for this table.'
        )

        return redirect(
            'create_order',
            table_id=table.id
        )

    new_order = Order.objects.create(
        table=table,
        order_type=previous_order.order_type,
        status='pending',
        kitchen_status='waiting',
        printer_route=previous_order.printer_route,
        notes=f'Repeated from Order #{previous_order.id}.'
    )

    for item in previous_order.items.all():

        _copy_item_to_order(
            item,
            new_order
        )

    new_order.save()
    table.status = 'occupied'
    table.save(
        update_fields=['status']
    )

    messages.success(
        request,
        f'Order #{previous_order.id} repeated.'
    )

    return redirect(
        'order_detail',
        order_id=new_order.id
    )


# =====================================
# VOID / REFUND
# =====================================

@permission_required(
    'orders',
    'edit'
)
def void_order(
    request,
    order_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    if request.method == 'POST':

        order.status = 'cancelled'
        order.kitchen_status = 'cancelled'
        order.void_reason = request.POST.get(
            'reason',
            ''
        ).strip() or 'No reason provided'
        order.save()
        _refresh_table_status(order.table)

        messages.success(
            request,
            f'Order #{order.id} voided.'
        )

    return redirect(
        'tables'
    )


@permission_required(
    'orders',
    'edit'
)
def refund_order(
    request,
    order_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    if request.method == 'POST':

        order.refund_reason = request.POST.get(
            'reason',
            ''
        ).strip() or 'No reason provided'
        order.payment_method = 'split'
        order.is_paid = False
        order.save()

        for payment in order.payments.all():

            payment.status = 'refunded'
            payment.refunded_amount = payment.amount
            payment.notes = order.refund_reason
            payment.save()

        messages.success(
            request,
            f'Order #{order.id} refunded.'
        )

    return redirect(
        'generate_bill',
        order_id=order.id
    )


# =====================================
# COMPLETE ORDER
# =====================================

@permission_required(
    'orders',
    'edit'
)
def complete_order(
    request,
    order_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    order.status = 'completed'

    order.completed_at = timezone.now()

    order.save()

    order.table.status = 'free'

    order.table.save()

    return redirect(
        'tables'
    )
