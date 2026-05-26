from decimal import Decimal
from decimal import InvalidOperation

from django.contrib import messages
from django.utils import timezone
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from orders.models import (
    Order,
    OrderItem
)

from billing.models import (
    Payment
)

from permissionsapp.utils import (
    permission_required
)

from inventory.services import InventoryService
from settingsapp.models import SystemSettings


def _safe_decimal(value):

    try:

        return Decimal(value or '0')

    except InvalidOperation:

        return Decimal('0')


def _convert_received(amount, currency, settings):

    currency = (currency or 'BASE').upper()

    if not settings or currency in ['BASE', settings.currency.upper()]:

        return amount

    if currency == 'USD':

        return amount * settings.usd_to_base_rate

    if currency == 'RUB':

        return amount * settings.rub_to_base_rate

    return amount


def _currency_symbol(settings):

    currency = (
        settings.currency
        if settings
        else 'UZS'
    ).upper()

    return {
        'USD': '$',
        'RUB': '₽',
        'UZS': '',
    }.get(
        currency,
        currency
    )


def _paid_total(order):

    paid = sum(
        (
            payment_item.amount
            for payment_item in order.payments.filter(status='paid')
        ),
        Decimal('0')
    )
    refunded = sum(
        (
            payment_item.amount
            for payment_item in order.payments.filter(status='refunded')
        ),
        Decimal('0')
    )
    return max(
        paid - refunded,
        Decimal('0')
    )


# =====================================
# CASHIER DASHBOARD
# =====================================

@permission_required(
    'cashier',
    'view'
)
def cashier_dashboard(request):

    orders = Order.objects.filter(
        status__in=[
            'ready',
            'served'
        ]
    ).order_by(
        '-id'
    )

    total_sales = Payment.objects.filter(
        status='paid'
    ).count()

    context = {

        'orders': orders,

        'total_sales': total_sales,

    }

    return render(
        request,
        'cashier/dashboard.html',
        context
    )


# =====================================
# GENERATE BILL
# =====================================

@permission_required(
    'cashier',
    'edit'
)
def generate_bill(
    request,
    order_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    next_url = request.GET.get(
        'next'
    ) or request.POST.get(
        'next'
    ) or ''

    total = Decimal('0')

    for item in order.items.all():

        total += item.get_total()

    payment = order.payments.order_by(
        '-created_at'
    ).first()

    paid_amount = _paid_total(order)

    receipt_map = {}
    receipt_lines = []

    for item in order.items.all():

        if item.refunded or item.quantity <= 0:

            continue

        notes = item.notes or ''

        if notes.startswith('Combo:'):

            combo_name = notes.replace('Combo:', '', 1).strip()
            key = f'combo:{combo_name}'

            if key not in receipt_map:

                receipt_map[key] = {
                    'name': combo_name,
                    'quantity': 1,
                    'total': Decimal('0'),
                    'note': '',
                }

            receipt_map[key]['total'] += item.get_total()
            continue

        receipt_lines.append(
            {
                'name': item.menu_item.name,
                'quantity': item.quantity,
                'total': item.get_total(),
                'note': notes,
            }
        )

    receipt_lines = list(receipt_map.values()) + receipt_lines

    selected_method = (
        request.POST.get('method')
        or order.payment_method
        or (
            payment.method
            if payment
            else 'cash'
        )
    )

    cash_received = Decimal('0')
    change_due = Decimal('0')
    payment_error = None
    system_settings = SystemSettings.objects.select_related(
        'restaurant',
        'branch'
    ).first()

    if request.method == 'POST':

        selected_method = request.POST.get(
            'method',
            'cash'
        )

        try:

            cash_received = Decimal(
                request.POST.get(
                    'cash_received',
                    '0'
                ) or '0'
            )

        except InvalidOperation:

            cash_received = Decimal('0')

        split_rows = []

        for method in [
            'cash',
            'card',
            'click',
            'payme'
        ]:

            amount = _safe_decimal(
                request.POST.get(
                    f'split_{method}',
                    '0'
                )
            )

            if amount > 0:

                split_rows.append(
                    (
                        method,
                        amount
                    )
                )

        if split_rows:

            split_total = sum(
                (
                    amount
                    for method, amount in split_rows
                ),
                Decimal('0')
            )

            if split_total < total:

                payment_error = (
                    'Split payment totaldan kam.'
                )

            else:

                change_due = split_total - total

        elif selected_method == 'cash':

            received_currency = request.POST.get(
                'cash_received_currency',
                'BASE'
            )
            converted_received = _convert_received(
                cash_received,
                received_currency,
                system_settings
            )
            change_due = converted_received - total

            if converted_received < total:

                payment_error = (
                    'Naqd summa totaldan kam.'
                )

        if not payment_error:

            if split_rows:

                order.payments.filter(
                    status='pending'
                ).delete()

                for method, amount in split_rows:

                    Payment.objects.create(
                        order=order,
                        amount=amount,
                        method=method,
                        status='paid',
                        provider_response={
                            'split_total': str(total),
                            'change_due': str(change_due)
                        }
                    )

                payment = order.payments.order_by(
                    '-created_at'
                ).first()

            else:

                payment = Payment.objects.create(
                    order=order,
                    amount=total,
                    method=selected_method,
                    status='paid',
                    provider_response={
                        'cash_received': str(cash_received),
                        'cash_received_currency': request.POST.get(
                            'cash_received_currency',
                            'BASE'
                        ),
                        'converted_received': str(
                            _convert_received(
                                cash_received,
                                request.POST.get(
                                    'cash_received_currency',
                                    'BASE'
                                ),
                                system_settings
                            )
                        ),
                        'change_due': str(
                            max(
                                change_due,
                                Decimal('0')
                            )
                        )
                    }
                )

            order.payment_method = (
                'split'
                if split_rows
                else selected_method
            )
            order.is_paid = True
            order.status = 'completed'
            order.completed_at = timezone.now()
            order.save()

            InventoryService.deduct_order_inventory(order)

            if order.table.table_number == 0:

                order.table.status = 'free'

            else:

                order.table.status = 'cleaning'

            order.table.save(
                update_fields=['status']
            )

            messages.success(
                request,
                'Payment completed.'
            )

            if next_url:

                return redirect(next_url)

            return redirect('cashier_dashboard')

    elif payment and payment.provider_response:

        try:

            cash_received = Decimal(
                payment.provider_response.get(
                    'cash_received',
                    '0'
                )
            )

            change_due = Decimal(
                payment.provider_response.get(
                    'change_due',
                    '0'
                )
            )

        except InvalidOperation:

            cash_received = Decimal('0')
            change_due = Decimal('0')

    context = {

        'order': order,

        'receipt_lines': receipt_lines,

        'payment': payment,

        'total': total,

        'selected_method': selected_method,

        'cash_received': cash_received,

        'change_due': max(
            change_due,
            Decimal('0')
        ),

        'payment_error': payment_error,

        'paid_amount': paid_amount,

        'remaining_amount': max(
            total - paid_amount,
            Decimal('0')
        ),

        'tip_10': total * Decimal('0.10'),

        'tip_15': total * Decimal('0.15'),

        'tip_20': total * Decimal('0.20'),

        'next_url': next_url,

        'system_settings': system_settings,

        'currency_symbol': _currency_symbol(system_settings),

        'adjustable_items': order.items.filter(
            refunded=False,
            quantity__gt=0
        ).select_related(
            'menu_item'
        ),

    }

    return render(
        request,
        'cashier/bill.html',
        context
    )


@permission_required(
    'cashier',
    'edit'
)
def refund_order_item(
    request,
    order_id,
    item_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    item = get_object_or_404(
        OrderItem,
        id=item_id,
        order=order
    )

    if request.method != 'POST':

        return redirect(
            'generate_bill',
            order_id=order.id
        )

    reason = request.POST.get(
        'reason',
        ''
    ).strip()
    try:

        quantity_to_reduce = int(
            request.POST.get(
                'quantity',
                '1'
            ) or 1
        )

    except (TypeError, ValueError):

        quantity_to_reduce = 1
    quantity_to_reduce = max(
        1,
        min(
            quantity_to_reduce,
            item.quantity
        )
    )

    current_total = item.get_total()
    unit_total = (
        current_total / item.quantity
        if item.quantity
        else Decimal('0')
    )
    refund_amount = unit_total * quantity_to_reduce

    if quantity_to_reduce >= item.quantity:

        item.refunded = True
        item.refund_amount = current_total
        item.save(
            update_fields=[
                'refunded',
                'refund_amount'
            ]
        )

    else:

        item.quantity -= quantity_to_reduce
        item.refund_amount += refund_amount
        item.save(
            update_fields=[
                'quantity',
                'refund_amount'
            ]
        )

    if refund_amount > 0:

        last_paid = order.payments.filter(
            status='paid'
        ).order_by(
            '-created_at'
        ).first()

        Payment.objects.create(
            order=order,
            amount=refund_amount,
            method=(
                last_paid.method
                if last_paid
                else order.payment_method or 'cash'
            ),
            status='refunded',
            notes=(
                reason
                or f'{item.menu_item.name} quantity reduced by {quantity_to_reduce}'
            ),
            provider_response={
                'item_id': item.id,
                'quantity': quantity_to_reduce,
                'reason': reason,
            }
        )

    order.save()

    messages.success(
        request,
        (
            f'{item.menu_item.name} ×{quantity_to_reduce} '
            f'adjusted/refunded.'
        )
    )

    return redirect(
        'generate_bill',
        order_id=order.id
    )
