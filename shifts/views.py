from decimal import Decimal
from decimal import InvalidOperation

from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from billing.models import Payment

from orders.models import Order

from settingsapp.views import _build_simple_xlsx

from .models import Shift, ShiftLog, CashMovement


def _safe_decimal(value):

    try:

        return Decimal(value or '0')

    except (InvalidOperation, TypeError):

        return Decimal('0')


# =========================
# SHIFT DASHBOARD
# =========================

def shift_dashboard(request):

    active_shift = Shift.objects.filter(

        cashier=request.user,

        status='open'

    ).first()

    shifts = Shift.objects.order_by(

        '-opened_at'

    )[:10]

    active_clock = ShiftLog.objects.filter(
        employee=request.user,
        clock_out__isnull=True
    ).first()

    clock_logs = ShiftLog.objects.filter(
        employee=request.user
    ).order_by(
        '-clock_in'
    )[:10]

    cash_movements = CashMovement.objects.none()
    live_cash_sales = Decimal('0')
    live_total_sales = Decimal('0')
    live_cash_adjustments = Decimal('0')
    live_expected_cash = Decimal('0')
    payments_by_method = []

    if active_shift:

        cash_movements = active_shift.cash_movements.order_by(
            '-created_at'
        )[:10]

        payments_by_method = _shift_payments_by_method(active_shift)

        live_total_sales = sum(
            (
                row['total']
                for row in payments_by_method
            ),
            Decimal('0')
        )

        for row in payments_by_method:

            if row['method'] == 'cash':

                live_cash_sales = row['total']

        live_cash_adjustments = sum(
            (
                movement.signed_amount()
                for movement in active_shift.cash_movements.all()
            ),
            Decimal('0')
        )

        live_expected_cash = (
            active_shift.opening_cash
            + live_cash_sales
            + live_cash_adjustments
        )

    context = {

        'active_shift': active_shift,

        'shifts': shifts,

        'active_clock': active_clock,

        'clock_logs': clock_logs,

        'cash_movements': cash_movements,

        'payments_by_method': payments_by_method,

        'live_cash_sales': live_cash_sales,

        'live_total_sales': live_total_sales,

        'live_cash_adjustments': live_cash_adjustments,

        'live_expected_cash': live_expected_cash,

    }

    return render(

        request,

        'shifts/dashboard.html',

        context

    )


def clock_in(request):

    existing = ShiftLog.objects.filter(
        employee=request.user,
        clock_out__isnull=True
    ).first()

    if existing:

        messages.info(
            request,
            'Already clocked in.'
        )

        return redirect(
            'shift_dashboard'
        )

    ShiftLog.objects.create(
        employee=request.user,
        clock_in=timezone.now()
    )

    messages.success(
        request,
        'Clock in saved.'
    )

    return redirect(
        'shift_dashboard'
    )


def clock_out(request):

    active_clock = ShiftLog.objects.filter(
        employee=request.user,
        clock_out__isnull=True
    ).first()

    if not active_clock:

        messages.error(
            request,
            'No active clock log.'
        )

        return redirect(
            'shift_dashboard'
        )

    active_clock.clock_out = timezone.now()
    active_clock.save(
        update_fields=[
            'clock_out'
        ]
    )

    messages.success(
        request,
        'Clock out saved.'
    )

    return redirect(
        'shift_dashboard'
    )


# =========================
# OPEN SHIFT
# =========================

def open_shift(request):

    next_url = request.GET.get(
        'next'
    ) or request.POST.get(
        'next'
    ) or 'shift_dashboard'

    existing_shift = Shift.objects.filter(

        cashier=request.user,

        status='open'

    ).first()

    if existing_shift:

        messages.error(

            request,

            'You already have an open shift.'

        )

        return redirect(next_url)

    if request.method == 'POST':

        raw_opening_cash = request.POST.get(
            'opening_cash',
            ''
        )

        try:

            opening_cash = Decimal(
                raw_opening_cash
            )

        except Exception:

            opening_cash = Decimal('-1')

        if opening_cash < 0:

            messages.error(
                request,
                'Opening cash majburiy va 0 dan kichik bo‘lmasligi kerak.'
            )

            return redirect(
                f'/shifts/open/?next={next_url}'
            )

        Shift.objects.create(

            cashier=request.user,

            opening_cash=opening_cash,

            expected_cash=opening_cash,

            status='open'

        )

        messages.success(

            request,

            'Shift opened successfully.'

        )

        return redirect(next_url)

    return render(

        request,

        'shifts/open_shift.html',

        {
            'next_url': next_url
        }

    )


# =========================
# CLOSE SHIFT
# =========================

def close_shift(

    request,

    shift_id

):

    shift = get_object_or_404(

        Shift,

        id=shift_id

    )

    if shift.status == 'closed':

        messages.error(

            request,

            'Shift already closed.'

        )

        return redirect(
            'shift_dashboard'
        )

    if request.method == 'POST':

        closing_cash = _safe_decimal(
            request.POST.get('closing_cash')
        )

        # =========================
        # CASH PAYMENTS
        # =========================

        paid_payments = Payment.objects.filter(

            status='paid',

            created_at__gte=shift.opened_at

        )

        cash_payments = paid_payments.filter(

            method='cash',

        )

        total_cash_sales = Decimal('0')

        for payment in cash_payments:

            total_cash_sales += payment.amount

        cash_adjustments = sum(
            (
                movement.signed_amount()
                for movement in shift.cash_movements.all()
            ),
            Decimal('0')
        )


        # =========================
        # TOTAL ORDERS
        # =========================

        total_sales = sum(
            (
                payment.amount
                for payment in paid_payments
            ),
            Decimal('0')
        )

        total_orders = Order.objects.filter(

            created_at__gte=shift.opened_at,

            is_paid=True

        ).count()


        # =========================
        # UPDATE SHIFT
        # =========================

        shift.total_sales = total_sales

        shift.total_orders = total_orders

        shift.expected_cash = (

            shift.opening_cash +

            total_cash_sales +

            cash_adjustments

        )


        # =========================
        # CLOSE SHIFT
        # =========================

        shift.close_shift(
            closing_cash
        )

        shift.save()


        messages.success(

            request,

            'Shift closed successfully.'

        )

        return redirect(
            'shift_dashboard'
        )

    payments_by_method = _shift_payments_by_method(shift)

    total_sales = sum(
        (
            row['total']
            for row in payments_by_method
        ),
        Decimal('0')
    )

    cash_sales = sum(
        (
            row['total']
            for row in payments_by_method
            if row['method'] == 'cash'
        ),
        Decimal('0')
    )

    cash_adjustments = sum(
        (
            movement.signed_amount()
            for movement in shift.cash_movements.all()
        ),
        Decimal('0')
    )

    expected_cash = _shift_expected_cash(shift)

    return render(

        request,

        'shifts/close_shift.html',

        {

            'shift': shift,

            'payments_by_method': payments_by_method,

            'cash_movements': shift.cash_movements.order_by('-created_at'),

            'expected_cash': expected_cash,

            'total_sales': total_sales,

            'cash_sales': cash_sales,

            'cash_adjustments': cash_adjustments,

        }

    )


def _shift_payments_by_method(shift):

    rows = []

    for method in [
        'cash',
        'card',
        'click',
        'payme',
    ]:

        total = sum(
            (
                payment.amount
                for payment in Payment.objects.filter(
                    method=method,
                    status='paid',
                    created_at__gte=shift.opened_at
                )
            ),
            Decimal('0')
        )

        rows.append(
            {
                'method': method,
                'total': total,
            }
        )

    return rows


def _shift_expected_cash(shift):

    cash_sales = sum(
        (
            payment.amount
            for payment in Payment.objects.filter(
                method='cash',
                status='paid',
                created_at__gte=shift.opened_at
            )
        ),
        Decimal('0')
    )

    adjustments = sum(
        (
            movement.signed_amount()
            for movement in shift.cash_movements.all()
        ),
        Decimal('0')
    )

    return shift.opening_cash + cash_sales + adjustments


def cash_movement(request, shift_id):

    shift = get_object_or_404(
        Shift,
        id=shift_id,
        status='open'
    )

    if request.method != 'POST':

        return redirect(
            'shift_dashboard'
        )

    movement_type = request.POST.get(
        'movement_type',
        'in'
    )

    amount = _safe_decimal(
        request.POST.get('amount')
    )

    reason = request.POST.get(
        'reason',
        ''
    ).strip()

    if movement_type not in ['in', 'out'] or amount <= 0 or not reason:

        messages.error(
            request,
            'Cash in/out uchun summa va sabab majburiy.'
        )

        return redirect(
            'shift_dashboard'
        )

    CashMovement.objects.create(
        shift=shift,
        movement_type=movement_type,
        amount=amount,
        reason=reason,
        created_by=request.user
    )

    messages.success(
        request,
        'Cash movement saqlandi.'
    )

    return redirect(
        'shift_dashboard'
    )


def shift_report_excel(request, shift_id):

    shift = get_object_or_404(
        Shift,
        id=shift_id
    )

    rows = [
        ['Shift', shift.id],
        ['Cashier', shift.cashier.username],
        ['Status', shift.status],
        ['Opened At', shift.opened_at],
        ['Closed At', shift.closed_at or ''],
        ['Opening Cash', shift.opening_cash],
        ['Expected Cash', shift.expected_cash or _shift_expected_cash(shift)],
        ['Closing Cash', shift.closing_cash or ''],
        ['Difference', shift.difference],
        [],
        ['Payment Method', 'Total'],
    ]

    for row in _shift_payments_by_method(shift):

        rows.append(
            [
                row['method'].upper(),
                row['total']
            ]
        )

    rows.extend(
        [
            [],
            ['Cash Movement', 'Amount', 'Reason', 'By', 'At'],
        ]
    )

    for movement in shift.cash_movements.order_by('created_at'):

        rows.append(
            [
                movement.get_movement_type_display(),
                movement.signed_amount(),
                movement.reason,
                movement.created_by.username if movement.created_by else '',
                movement.created_at,
            ]
        )

    response = HttpResponse(
        _build_simple_xlsx(rows),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = (
        f'attachment; filename="shift-{shift.id}-report.xlsx"'
    )

    return response
