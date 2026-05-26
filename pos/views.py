from decimal import Decimal
from datetime import datetime
from datetime import time
from datetime import timedelta

from django.db.models import Q
from django.db.models import Sum
from django.db import transaction
from django.utils import timezone
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib import messages

from accounts.models import User
from menu.models import MenuItem
from menu.models import ComboMeal
from menu.models import ModifierOption
from menu.models import ProductVariant

from orders.models import (
    Order,
    OrderItem,
    OrderItemModifier,
    Table
)

from billing.models import Payment

from permissionsapp.utils import (
    permission_required
)

from reservations.models import Reservation
from reservations.services import send_due_reservation_reminders
from reservations.services import send_reservation_confirmation

from shifts.models import Shift
from settingsapp.models import SystemSettings
from inventory.services import InventoryService


# =====================================
# GLOBAL CART
# =====================================

CART = []

HELD_ORDERS = []


ACTIVE_ORDER_STATUSES = [
    'pending',
    'held',
    'preparing',
    'ready',
    'served',
]


def _active_shift(request):

    return Shift.objects.filter(
        cashier=request.user,
        status='open'
    ).first()


def _require_shift(request):

    shift = _active_shift(request)

    if shift:

        return shift

    messages.error(
        request,
        'Avval kassani oching va opening cash kiriting.'
    )

    return None


def _available_menu_items():

    now_time = timezone.localtime().time()

    return MenuItem.objects.filter(
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


def _system_settings():

    return SystemSettings.objects.select_related(
        'restaurant',
        'branch'
    ).first()


def _currency_symbol(settings=None):

    currency = (
        (settings.currency if settings else 'UZS')
        or 'UZS'
    ).upper()

    return {
        'USD': '$',
        'RUB': '₽',
        'UZS': 'so‘m',
    }.get(
        currency,
        currency
    )


def _convert_received_to_base(amount, currency, settings=None):

    settings = settings or _system_settings()
    currency = (currency or 'BASE').upper()

    if currency in ['BASE', settings.currency.upper() if settings else 'UZS']:

        return amount

    if currency == 'USD':

        return amount * (
            settings.usd_to_base_rate
            if settings
            else Decimal('12020')
        )

    if currency == 'RUB':

        return amount * (
            settings.rub_to_base_rate
            if settings
            else Decimal('135')
        )

    return amount


def _expire_old_reservations():

    now = timezone.now()
    expired = Reservation.objects.select_related(
        'table'
    ).filter(
        status='confirmed',
        reservation_time__lt=now - timedelta(minutes=30)
    )

    for reservation in expired:

        has_order = Order.objects.filter(
            table=reservation.table,
            created_at__gte=reservation.reservation_time - timedelta(minutes=30),
            status__in=ACTIVE_ORDER_STATUSES
        ).exists()

        if has_order:

            continue

        reservation.status = 'cancelled'
        reservation.save(
            update_fields=[
                'status'
            ]
        )

        if reservation.table.status == 'reserved':

            reservation.table.status = 'free'
            reservation.table.save(
                update_fields=[
                    'status'
                ]
            )


def _current_waiter(request):

    if (
        request.user.is_authenticated
        and getattr(request.user, 'is_waiter', False)
    ):

        return request.user

    waiter_id = request.session.get('pos_waiter_id')

    if not waiter_id:

        return None

    return User.objects.filter(
        id=waiter_id,
        status='active'
    ).select_related(
        'role'
    ).first()


def _find_waiter_by_pin(pin):

    if not pin:

        return None

    return User.objects.filter(
        waiter_pin=pin,
        status='active'
    ).filter(
        Q(role__name__icontains='waiter')
        | Q(role__name__icontains='server')
        | Q(is_staff=True)
    ).select_related(
        'role'
    ).first()


def _open_table_order(table, waiter=None):

    order = Order.objects.filter(
        table=table,
        status__in=ACTIVE_ORDER_STATUSES,
        is_paid=False
    ).order_by(
        '-created_at'
    ).first()

    if order:

        if waiter and not order.waiter_id:

            order.waiter = waiter
            order.save(
                update_fields=[
                    'waiter'
                ]
            )

        return order

    order = Order.objects.create(
        table=table,
        restaurant=table.restaurant,
        branch=table.branch,
        waiter=waiter,
        order_type='dine_in',
        status='pending',
        kitchen_status='waiting'
    )

    table.status = 'occupied'
    table.save(
        update_fields=[
            'status'
        ]
    )

    return order


# =====================================
# POS TERMINAL
# =====================================

@permission_required(
    'pos',
    'view'
)
def pos_terminal(request):

    shift = _require_shift(request)

    if not shift:

        return redirect(
            '/shifts/open/?next=/pos/'
        )

    active_order = None
    table_id = request.GET.get('table')
    direct_mode = (
        request.GET.get('direct') == '1'
        or bool(CART)
    )

    if table_id:

        table = get_object_or_404(
            Table,
            id=table_id,
            is_active=True
        )

        active_order = _open_table_order(
            table,
            waiter=_current_waiter(request)
        )

        Reservation.objects.filter(
            table=table,
            status='confirmed'
        ).update(
            status='seated'
        )

    menu_items = _available_menu_items().prefetch_related(
        'variants',
        'modifier_groups__options'
    )

    combo_meals = ComboMeal.objects.filter(
        is_active=True
    ).prefetch_related(
        'items'
    ).order_by(
        'name'
    )

    tables = Table.objects.filter(
        is_active=True
    ).exclude(
        table_number=0
    ).order_by(
        'table_number'
    )

    categories = [
        ('all', 'All'),
        ('fast_food', 'Food'),
        ('beverage', 'Drinks'),
        ('main', 'Main'),
        ('dessert', 'Dessert'),
        ('combo', 'Combo'),
    ]

    total = Decimal('0')
    cart_items = CART
    settings = _system_settings()

    if active_order:

        cart_items = active_order.items.select_related(
            'menu_item',
            'variant'
        ).prefetch_related(
            'modifiers__modifier_option'
        )
        total = active_order.calculate_total()

    else:

        for item in CART:

            total += item['subtotal']

    context = {

        'menu_items': menu_items,

        'combo_meals': combo_meals,

        'cart_items': cart_items,

        'total': total,

        'held_orders': HELD_ORDERS,

        'tables': tables,

        'categories': categories,

        'active_order': active_order,

        'active_shift': shift,

        'direct_mode': direct_mode,

        'current_waiter': _current_waiter(request),

        'system_settings': settings,

        'currency_symbol': _currency_symbol(settings),

    }

    return render(
        request,
        'pos/terminal.html',
        context
    )


@permission_required(
    'pos',
    'view'
)
def open_table_register(request, table_id):

    shift = _require_shift(request)

    if not shift:

        return redirect(
            '/shifts/open/?next=/pos/'
        )

    table = get_object_or_404(
        Table,
        id=table_id,
        is_active=True
    )

    if table.status == 'cleaning':

        messages.error(
            request,
            'Bu stol cleaning holatida. Avval free qiling.'
        )

        return redirect(
            'pos_terminal'
        )

    _open_table_order(
        table,
        waiter=_current_waiter(request)
    )

    return redirect(
        f'/pos/?table={table.id}'
    )


@permission_required(
    'pos',
    'edit'
)
def mark_table_free(request, table_id):

    table = get_object_or_404(
        Table,
        id=table_id,
        is_active=True
    )

    table.status = 'free'
    table.save(
        update_fields=[
            'status'
        ]
    )

    messages.success(
        request,
        f'Table {table.table_number} free qilindi.'
    )

    return redirect(
        'pos_terminal'
    )


@permission_required(
    'pos',
    'view'
)
def waiter_pin_login(request):

    if request.method != 'POST':

        return redirect(
            'pos_terminal'
        )

    waiter = _find_waiter_by_pin(
        request.POST.get('waiter_pin', '').strip()
    )

    if not waiter:

        messages.error(
            request,
            'Waiter PIN topilmadi.'
        )

        return redirect(
            request.POST.get('next') or 'pos_terminal'
        )

    request.session['pos_waiter_id'] = waiter.id

    messages.success(
        request,
        f'Waiter: {waiter.get_full_name() or waiter.username}'
    )

    return redirect(
        request.POST.get('next') or 'pos_terminal'
    )


@permission_required(
    'pos',
    'view'
)
def waiter_pin_logout(request):

    request.session.pop(
        'pos_waiter_id',
        None
    )

    messages.success(
        request,
        'Waiter session yopildi.'
    )

    return redirect(
        'pos_terminal'
    )


@permission_required(
    'pos',
    'view'
)
def waiter_commission_dashboard(request):

    today = timezone.localdate()
    settings = SystemSettings.objects.first()
    percent = (
        settings.waiter_commission_percent
        if settings
        else Decimal('1')
    )
    fixed_pay = (
        settings.waiter_daily_fixed_pay
        if settings
        else Decimal('50000')
    )
    selected_date = request.GET.get('date') or str(today)
    waiter_filter = request.GET.get('waiter') or ''
    role_name = (
        getattr(getattr(request.user, 'role', None), 'name', '') or ''
    ).lower()
    can_view_all_waiters = (
        request.user.is_superuser
        or request.user.is_staff
        or any(
            token in role_name
            for token in [
                'admin',
                'manager',
                'cashier',
                'owner',
            ]
        )
    )

    try:

        report_date = datetime.strptime(
            selected_date,
            '%Y-%m-%d'
        ).date()

    except Exception:

        report_date = today

    waiters = User.objects.filter(
        Q(role__name__icontains='waiter')
        | Q(role__name__icontains='server')
    ).select_related(
        'role'
    ).order_by(
        'first_name',
        'username'
    )

    if not can_view_all_waiters:

        waiters = waiters.filter(
            id=request.user.id
        )
        waiter_filter = str(request.user.id)

    if waiter_filter:

        waiters = waiters.filter(
            id=waiter_filter
        )

    rows = []

    for waiter in waiters:

        orders = Order.objects.filter(
            waiter=waiter,
            is_paid=True,
            completed_at__date=report_date
        )
        sales = orders.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')

        rows.append(
            {
                'waiter': waiter,
                'order_count': orders.count(),
                'sales': sales,
                'commission': sales * percent / Decimal('100'),
                'fixed_pay': fixed_pay,
                'total_payout': fixed_pay + (
                    sales * percent / Decimal('100')
                )
            }
        )

    return render(
        request,
        'pos/waiters.html',
        {
            'rows': rows,
            'commission_percent': percent,
            'fixed_pay': fixed_pay,
            'today': today,
            'report_date': report_date,
            'waiters': User.objects.filter(
                Q(role__name__icontains='waiter')
                | Q(role__name__icontains='server')
            ).order_by('first_name', 'username'),
            'selected_waiter': waiter_filter,
            'currency_symbol': _currency_symbol(settings),
            'can_view_all_waiters': can_view_all_waiters,
        }
    )


@permission_required(
    'pos',
    'edit'
)
def add_to_order_cart(request, order_id, product_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        is_paid=False
    )

    product = get_object_or_404(
        MenuItem,
        id=product_id
    )

    if request.method == 'POST':

        variant = None
        variant_id = request.POST.get('variant')

        if variant_id:

            variant = get_object_or_404(
                ProductVariant,
                id=variant_id,
                menu_item=product,
                available=True
            )

        item = OrderItem.objects.create(
            order=order,
            menu_item=product,
            variant=variant,
            quantity=1,
            course=request.POST.get('course') or 'main',
            guest_name=request.POST.get('guest_name') or '',
            notes=request.POST.get('notes') or '',
            kitchen_status='draft'
        )

        modifier_ids = request.POST.getlist(
            'modifiers'
        )

        for modifier in ModifierOption.objects.filter(
            id__in=modifier_ids
        ):

            OrderItemModifier.objects.create(
                order_item=item,
                modifier_option=modifier
            )

        order.save()

        return redirect(
            f'/pos/?table={order.table_id}'
        )

    item = order.items.filter(
        menu_item=product,
        variant__isnull=True,
        refunded=False,
        kitchen_status='draft'
    ).first()

    if item:

        item.quantity += 1
        item.save(
            update_fields=[
                'quantity'
            ]
        )

    else:

        OrderItem.objects.create(
            order=order,
            menu_item=product,
            quantity=1,
            kitchen_status='draft'
        )

    order.save()

    return redirect(
        f'/pos/?table={order.table_id}'
    )


@permission_required(
    'pos',
    'edit'
)
def apply_order_discount(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        is_paid=False
    )

    discount = Decimal('0')

    try:

        discount = Decimal(
            request.POST.get('discount_amount') or '0'
        )

    except Exception:

        discount = Decimal('-1')

    waiter_pin = request.POST.get(
        'waiter_pin',
        ''
    )

    waiter = _current_waiter(request) or _find_waiter_by_pin(waiter_pin)

    if discount < 0:

        messages.error(
            request,
            'Discount noto‘g‘ri.'
        )

        return redirect(
            f'/pos/?table={order.table_id}'
        )

    if discount > 0 and not (
        request.user.is_superuser
        or waiter
    ):

        messages.error(
            request,
            'Discount uchun waiter PIN kerak.'
        )

        return redirect(
            f'/pos/?table={order.table_id}'
        )

    order.discount_amount = discount

    if waiter and not order.waiter_id:

        order.waiter = waiter

    order.save()

    messages.success(
        request,
        'Discount saqlandi.'
    )

    return redirect(
        f'/pos/?table={order.table_id}'
    )


@permission_required(
    'pos',
    'edit'
)
def add_combo_to_pos_order(request, order_id, combo_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        is_paid=False
    )

    combo = get_object_or_404(
        ComboMeal,
        id=combo_id,
        is_active=True
    )

    combo_items = list(
        combo.items.all()
    )

    selected_items = []
    regular_total = Decimal('0')
    extra_total = Decimal('0')

    for menu_item in combo_items:

        selected = menu_item

        if request.method == 'POST':

            replacement_id = request.POST.get(
                f'combo_item_{menu_item.id}'
            )

            if replacement_id:

                selected = get_object_or_404(
                    MenuItem,
                    id=replacement_id,
                    available=True
                )

        selected_items.append(
            (
                menu_item,
                selected
            )
        )

        regular_total += selected.price

        if selected.price > menu_item.price:

            extra_total += selected.price - menu_item.price

    target_total = combo.get_total_price() + extra_total

    for original_item, menu_item in selected_items:

        replacement_note = ''

        if original_item.id != menu_item.id:

            diff = max(
                menu_item.price - original_item.price,
                Decimal('0')
            )
            replacement_note = (
                f' | replaced {original_item.name}'
                f' (+{diff})'
            )

        OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=1,
            kitchen_status='draft',
            course=(
                menu_item.category
                if menu_item.category in ['starter', 'dessert']
                else 'main'
            ),
            notes=(
                f'Combo: {combo.name} '
                f'({combo.discount_percent}% off)'
                f'{replacement_note}'
            )
        )

    combo_discount = max(
        regular_total - target_total,
        Decimal('0')
    )

    order.discount_amount = (
        order.discount_amount or Decimal('0')
    ) + combo_discount
    order.notes = (
        (order.notes or '')
        + f'\nCombo added: {combo.name}'
    ).strip()
    order.save()

    messages.success(
        request,
        f'{combo.name} combo qo‘shildi.'
    )

    return redirect(
        f'/pos/?table={order.table_id}'
    )


@permission_required(
    'pos',
    'edit'
)
def adjust_order_cart_item(request, item_id, action):

    item = get_object_or_404(
        OrderItem,
        id=item_id
    )

    order = item.order

    if action == 'increase':

        item.quantity += 1
        item.save(
            update_fields=[
                'quantity'
            ]
        )

    elif action == 'decrease':

        if item.quantity > 1:

            item.quantity -= 1
            item.save(
                update_fields=[
                    'quantity'
                ]
            )

        else:

            item.delete()

    order.save()

    return redirect(
        f'/pos/?table={order.table_id}'
    )


@permission_required(
    'pos',
    'view'
)
def pos_orders(request):

    shift = _require_shift(request)

    if not shift:

        return redirect(
            '/shifts/open/?next=/pos/'
        )

    orders = Order.objects.select_related(
        'table'
    ).prefetch_related(
        'items'
    ).order_by(
        '-created_at'
    )[:100]

    return render(
        request,
        'pos/orders.html',
        {
            'orders': orders,
            'active_shift': shift,
        }
    )


@permission_required(
    'pos',
    'view'
)
def pos_reservations(request):

    _expire_old_reservations()
    reminder_result = send_due_reservation_reminders()

    if reminder_result['failed']:

        messages.warning(
            request,
            'Baʼzi reservation reminderlar yuborilmadi: '
            + '; '.join(reminder_result['errors'][:2])
        )

    if request.method == 'POST':

        table = get_object_or_404(
            Table,
            id=request.POST.get('table'),
            is_active=True
        )
        reservation_date = request.POST.get('reservation_date')
        start_time = request.POST.get('reservation_time')
        end_time_value = request.POST.get('end_time')

        try:

            start_dt = timezone.make_aware(
                datetime.combine(
                    datetime.strptime(reservation_date, '%Y-%m-%d').date(),
                    datetime.strptime(start_time, '%H:%M').time()
                )
            )
            end_dt = None

            if end_time_value:

                end_dt = timezone.make_aware(
                    datetime.combine(
                        datetime.strptime(reservation_date, '%Y-%m-%d').date(),
                        datetime.strptime(end_time_value, '%H:%M').time()
                    )
                )

        except Exception:

            messages.error(
                request,
                'Reservation vaqti noto‘g‘ri.'
            )

            return redirect(
                'pos_reservations'
            )

        reservation = Reservation.objects.create(
            customer_name=request.POST.get(
                'customer_name',
                ''
            ).strip() or 'Guest',
            phone_number=request.POST.get(
                'phone_number',
                ''
            ).strip(),
            table=table,
            reservation_time=start_dt,
            end_time=end_dt,
            guest_count=int(
                request.POST.get('guest_count') or table.seats or 1
            ),
            status='confirmed'
        )

        table.status = 'reserved'
        table.save(
            update_fields=[
                'status'
            ]
        )

        messages.success(
            request,
            f'Table {table.table_number} bron qilindi.'
        )

        ok, reminder_message = send_reservation_confirmation(reservation)

        if ok:

            messages.success(
                request,
                'Staffga Telegram bron xabari yuborildi.'
            )

        else:

            messages.warning(
                request,
                reminder_message
            )

        return redirect(
            'pos_reservations'
        )

    reservations = Reservation.objects.select_related(
        'table'
    ).exclude(
        status='cancelled'
    ).order_by(
        'reservation_time'
    )

    calendar_hours = list(
        range(10, 24)
    )

    reservation_rows = []

    for reservation in reservations:

        start_hour = timezone.localtime(
            reservation.reservation_time
        ).hour + timezone.localtime(
            reservation.reservation_time
        ).minute / 60
        end_dt = reservation.end_time or (
            reservation.reservation_time + timedelta(hours=2)
        )
        end_hour = timezone.localtime(end_dt).hour + timezone.localtime(end_dt).minute / 60
        offset = max(
            min(
                (start_hour - 10) / 13 * 100,
                100
            ),
            0
        )
        width = max(
            (end_hour - start_hour) / 13 * 100,
            8
        )
        reservation_rows.append(
            {
                'reservation': reservation,
                'offset': offset,
                'width': min(width, 100 - offset)
            }
        )

    return render(
        request,
        'pos/reservations.html',
        {
            'reservations': reservations,
            'reservation_rows': reservation_rows,
            'calendar_hours': calendar_hours,
            'tables': Table.objects.filter(
                is_active=True
            ).exclude(
                table_number=0
            ).order_by(
                'table_number'
            ),
            'reminder_result': reminder_result,
        }
    )


@permission_required(
    'pos',
    'edit'
)
def send_reservation_reminders_now(request):

    result = send_due_reservation_reminders(
        window_minutes=24 * 60
    )

    if result['sent']:

        messages.success(
            request,
            f"{result['sent']} ta reservation reminder yuborildi."
        )

    elif result['failed']:

        messages.error(
            request,
            '; '.join(result['errors'][:3])
        )

    else:

        messages.info(
            request,
            'Yuboriladigan yangi reservation reminder yo‘q.'
        )

    return redirect(
        'pos_reservations'
    )


@permission_required(
    'pos',
    'edit'
)
def open_reservation_order(request, reservation_id):

    reservation = get_object_or_404(
        Reservation.objects.select_related('table'),
        id=reservation_id
    )
    order = _open_table_order(
        reservation.table,
        waiter=_current_waiter(request)
    )
    reservation.status = 'seated'
    reservation.save(
        update_fields=[
            'status'
        ]
    )

    return redirect(
        f'/pos/?table={order.table_id}'
    )


# =====================================
# ADD TO CART
# =====================================

@permission_required(
    'pos',
    'edit'
)
def add_to_cart(
    request,
    product_id
):

    product = get_object_or_404(
        MenuItem,
        id=product_id
    )

    found = False

    for item in CART:

        if item['product'].id == product.id:

            item['quantity'] += 1

            item['subtotal'] = (
                item['product'].price *
                item['quantity']
            )

            found = True

            break

    if not found:

        CART.append({

            'product': product,

            'quantity': 1,

            'subtotal': product.price,

        })

    messages.success(
        request,
        f'{product.name} added to cart'
    )

    return redirect(
        '/pos/?direct=1'
    )


# =====================================
# CLEAR CART
# =====================================

@permission_required(
    'pos',
    'edit'
)
def clear_cart(request):

    CART.clear()

    messages.success(
        request,
        'Cart cleared'
    )

    return redirect(
        '/pos/?direct=1'
    )


# =====================================
# INCREASE QUANTITY
# =====================================

@permission_required(
    'pos',
    'edit'
)
def increase_quantity(
    request,
    index
):

    if 0 <= index < len(CART):

        CART[index]['quantity'] += 1

        CART[index]['subtotal'] = (
            CART[index]['product'].price *
            CART[index]['quantity']
        )

    return redirect(
        '/pos/?direct=1'
    )


# =====================================
# DECREASE QUANTITY
# =====================================

@permission_required(
    'pos',
    'edit'
)
def decrease_quantity(
    request,
    index
):

    if 0 <= index < len(CART):

        if CART[index]['quantity'] > 1:

            CART[index]['quantity'] -= 1

            CART[index]['subtotal'] = (
                CART[index]['product'].price *
                CART[index]['quantity']
            )

        else:

            CART.pop(index)

    return redirect(
        '/pos/?direct=1'
    )


# =====================================
# PAYMENT PAGE
# =====================================

@permission_required(
    'pos',
    'view'
)
def payment_page(request):

    total = Decimal('0')
    settings = _system_settings()

    for item in CART:

        total += item['subtotal']

    context = {

        'cart_items': CART,

        'total': total,

        'currency_symbol': _currency_symbol(settings),

    }

    return render(
        request,
        'pos/payment.html',
        context
    )


# =====================================
# COMPLETE PAYMENT
# =====================================

@permission_required(
    'pos',
    'edit'
)
def complete_payment(
    request,
    method
):

    if method not in [
        'cash',
        'card',
        'click',
        'payme'
    ]:

        messages.error(
            request,
            'Unknown payment method.'
        )

        return redirect(
            'pos_terminal'
        )

    if not CART:

        messages.error(
            request,
            'Cart is empty.'
        )

        return redirect(
            'pos_terminal'
        )

    total = sum(
        (
            item['subtotal']
            for item in CART
        ),
        Decimal('0')
    )

    cash_received = Decimal('0')
    change_due = Decimal('0')
    settings = _system_settings()

    if method == 'cash':

        try:

            cash_received = Decimal(
                request.POST.get(
                    'cash_received',
                    '0'
                ) or '0'
            )

        except Exception:

            cash_received = Decimal('0')

        received_currency = request.POST.get(
            'cash_received_currency',
            'BASE'
        )
        converted_received = _convert_received_to_base(
            cash_received,
            received_currency,
            settings
        )

        if converted_received < total:

            messages.error(
                request,
                'Naqd summa totaldan kam.'
            )

            return redirect(
                '/pos/?direct=1'
            )

        change_due = converted_received - total

    pos_table, created = Table.objects.get_or_create(
        table_number=0,
        defaults={
            'seats': 0,
            'status': 'free',
            'assigned_waiter': 'POS'
        }
    )

    with transaction.atomic():

        order = Order.objects.create(
            table=pos_table,
            restaurant=pos_table.restaurant,
            branch=pos_table.branch,
            waiter=_current_waiter(request),
            order_type='takeaway',
            status='completed',
            kitchen_status='served',
            payment_method=method,
            is_paid=True,
            completed_at=timezone.now()
        )

        for cart_item in CART:

            OrderItem.objects.create(
                order=order,
                menu_item=cart_item['product'],
                quantity=cart_item['quantity']
            )

        order.save()

        Payment.objects.create(
            order=order,
            amount=total,
            method=method,
            status='paid',
            provider_response={
                'cash_received': str(cash_received),
                'cash_received_currency': received_currency,
                'converted_received': str(
                    _convert_received_to_base(
                        cash_received,
                        received_currency,
                        settings
                    )
                ),
                'change_due': str(change_due),
                'source': 'pos_direct_sale'
            }
        )

        InventoryService.deduct_order_inventory(order)

        pos_table.status = 'free'
        pos_table.save(
            update_fields=[
                'status'
            ]
        )

    CART.clear()

    messages.success(
        request,
        (
            f'Payment completed via {method.upper()}. '
            f'Receipt #{order.id}'
        )
    )

    return redirect(
        'pos_terminal'
    )


# =====================================
# HOLD CART
# =====================================

@permission_required(
    'pos',
    'edit'
)
def hold_cart(request):

    if CART:

        HELD_ORDERS.append(
            CART.copy()
        )

        CART.clear()

        messages.success(
            request,
            'Order held successfully'
        )

    return redirect(
        '/pos/?direct=1'
    )


# =====================================
# RESUME HELD ORDER
# =====================================

@permission_required(
    'pos',
    'edit'
)
def resume_held_order(
    request,
    held_order_id
):

    if 0 <= held_order_id < len(HELD_ORDERS):

        CART.clear()

        for item in HELD_ORDERS[held_order_id]:

            CART.append(item)

        HELD_ORDERS.pop(
            held_order_id
        )

        messages.success(
            request,
            'Held order resumed'
        )

    return redirect(
        'pos_terminal'
    )


# =====================================
# CANCEL HELD ORDER
# =====================================

@permission_required(
    'pos',
    'edit'
)
def cancel_held_order(
    request,
    held_order_id
):

    if 0 <= held_order_id < len(HELD_ORDERS):

        HELD_ORDERS.pop(
            held_order_id
        )

        messages.success(
            request,
            'Held order cancelled'
        )

    return redirect(
        '/pos/?direct=1'
    )
