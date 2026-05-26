from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date

from accounts.models import User
from billing.models import Payment
from inventory.models import InventoryWaste
from inventory.models import Product
from inventory.models import Purchase
from orders.models import Order
from orders.models import OrderItem
from orders.models import Table
from permissionsapp.utils import permission_required
from settingsapp.models import SystemSettings
from shifts.models import CashMovement
from shifts.models import Shift
from shifts.models import ShiftLog


def _money_sum(queryset, field='amount'):

    return queryset.aggregate(total=Sum(field))['total'] or Decimal('0')


def _as_float(value):

    return float(value or 0)


def _date_range(request):

    today = timezone.localdate()
    start = parse_date(request.GET.get('from') or '') or today
    end = parse_date(request.GET.get('to') or '') or today

    if end < start:
        start, end = end, start

    return start, end


def _safe_total(order):

    try:
        return Decimal(order.calculate_total())
    except Exception:
        return Decimal(order.total_amount or 0)


def _user_label(user):

    return user.full_name or user.username or f'User #{user.id}'


@permission_required('analytics', 'view')
def analytics_dashboard(request):

    start_date, end_date = _date_range(request)
    settings = SystemSettings.objects.first()
    currency = getattr(settings, 'currency', 'UZS')
    commission_percent = Decimal(
        getattr(settings, 'waiter_commission_percent', 1) or 0
    )
    fixed_pay = Decimal(
        getattr(settings, 'waiter_daily_fixed_pay', 0) or 0
    )

    date_filter = {
        'created_at__date__gte': start_date,
        'created_at__date__lte': end_date,
    }

    paid_payments = Payment.objects.filter(
        status='paid',
        **date_filter
    ).select_related('order', 'order__waiter', 'order__table')

    refund_payments = Payment.objects.filter(
        status='refunded',
        **date_filter
    )

    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    ).select_related('waiter', 'table')

    paid_orders = orders.filter(is_paid=True)
    active_orders = orders.exclude(
        status__in=['completed', 'cancelled']
    )

    revenue = _money_sum(paid_payments)
    refunds = _money_sum(refund_payments)
    net_revenue = revenue - refunds
    order_count = paid_orders.count()
    average_check = net_revenue / order_count if order_count else Decimal('0')

    purchase_expenses = _money_sum(
        Purchase.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ),
        'total_amount'
    )

    cash_in = _money_sum(
        CashMovement.objects.filter(
            movement_type='in',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ),
        'amount'
    )
    cash_out = _money_sum(
        CashMovement.objects.filter(
            movement_type='out',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ),
        'amount'
    )
    cash_balance_delta = cash_in - cash_out
    net_profit = net_revenue + cash_balance_delta - purchase_expenses

    payment_rows = []
    payment_chart = {
        'labels': [],
        'values': [],
    }

    for method, label in Payment.METHOD_CHOICES:
        total = _money_sum(paid_payments.filter(method=method))
        payment_rows.append(
            {
                'method': label,
                'total': total,
            }
        )
        payment_chart['labels'].append(label)
        payment_chart['values'].append(_as_float(total))

    today = timezone.localdate()
    start_graph = today - timedelta(days=6)
    daily_sales_map = defaultdict(Decimal)
    for payment in Payment.objects.filter(
        status='paid',
        created_at__date__gte=start_graph,
        created_at__date__lte=today,
    ):
        daily_sales_map[payment.created_at.date()] += payment.amount

    sales_chart = {
        'labels': [],
        'values': [],
    }
    for offset in range(7):
        day = start_graph + timedelta(days=offset)
        sales_chart['labels'].append(day.strftime('%d.%m'))
        sales_chart['values'].append(_as_float(daily_sales_map[day]))

    hourly_sales_map = defaultdict(Decimal)
    for payment in paid_payments:
        hourly_sales_map[payment.created_at.hour] += payment.amount

    hourly_chart = {
        'labels': [f'{hour:02d}:00' for hour in range(8, 24)],
        'values': [_as_float(hourly_sales_map[hour]) for hour in range(8, 24)],
    }

    waiter_filter = {
        'role__name__iregex': r'(waiter|server|offitsiant)',
        'status': 'active',
    }
    waiters = User.objects.filter(**waiter_filter).select_related('role')

    waiter_rows = []
    waiter_chart = {
        'labels': [],
        'values': [],
    }

    for waiter in waiters:
        waiter_orders = paid_orders.filter(waiter=waiter)
        waiter_sales = sum((_safe_total(order) for order in waiter_orders), Decimal('0'))
        waiter_commission = waiter_sales * commission_percent / Decimal('100')
        waiter_fixed_pay = fixed_pay if waiter_orders.exists() else Decimal('0')
        total_payout = waiter_fixed_pay + waiter_commission
        open_log = ShiftLog.objects.filter(
            employee=waiter,
            clock_out__isnull=True
        ).order_by('-clock_in').first()

        row = {
            'name': _user_label(waiter),
            'role': waiter.role_name,
            'orders': waiter_orders.count(),
            'sales': waiter_sales,
            'commission': waiter_commission,
            'fixed_pay': waiter_fixed_pay,
            'total_payout': total_payout,
            'clock_in': open_log.clock_in if open_log else None,
            'is_online': waiter.is_online,
        }
        waiter_rows.append(row)
        waiter_chart['labels'].append(row['name'])
        waiter_chart['values'].append(_as_float(waiter_sales))

    waiter_rows = sorted(
        waiter_rows,
        key=lambda row: row['sales'],
        reverse=True
    )

    top_products = []
    for row in (
        OrderItem.objects
        .filter(order__in=paid_orders)
        .values('menu_item__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:8]
    ):
        top_products.append(
            {
                'name': row['menu_item__name'] or 'Unknown',
                'quantity': row['total_sold'] or 0,
            }
        )

    top_product_chart = {
        'labels': [row['name'] for row in top_products],
        'values': [row['quantity'] for row in top_products],
    }

    table_status_rows = []
    for status, label in Table.STATUS_CHOICES:
        table_status_rows.append(
            {
                'status': label,
                'count': Table.objects.filter(status=status).count(),
            }
        )

    kitchen_status_rows = [
        {
            'status': 'Waiting',
            'count': Order.objects.filter(kitchen_status='waiting').count(),
        },
        {
            'status': 'Preparing',
            'count': Order.objects.filter(kitchen_status='preparing').count(),
        },
        {
            'status': 'Ready',
            'count': Order.objects.filter(kitchen_status='ready').count(),
        },
    ]

    low_stock_rows = Product.objects.filter(
        quantity__lte=10
    ).order_by('quantity')[:6]

    most_wasted_products = (
        InventoryWaste.objects
        .filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
        .values('product__name')
        .annotate(total_waste=Sum('quantity'))
        .order_by('-total_waste')[:5]
    )

    open_shifts = Shift.objects.filter(status='open')
    closed_shift_count = Shift.objects.filter(
        status='closed',
        closed_at__date__gte=start_date,
        closed_at__date__lte=end_date,
    ).count()

    busiest_table_rows = []
    for table in Table.objects.all().order_by('table_number')[:12]:
        table_orders = paid_orders.filter(table=table)
        total = sum((_safe_total(order) for order in table_orders), Decimal('0'))
        if table_orders.exists() or table.status != 'free':
            busiest_table_rows.append(
                {
                    'table': table.table_number,
                    'status': table.get_status_display(),
                    'orders': table_orders.count(),
                    'total': total,
                }
            )

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'currency': currency,
        'commission_percent': commission_percent,
        'fixed_pay': fixed_pay,
        'revenue': net_revenue,
        'gross_revenue': revenue,
        'refunds': refunds,
        'net_profit': net_profit,
        'purchase_expenses': purchase_expenses,
        'cash_balance_delta': cash_balance_delta,
        'cash_in': cash_in,
        'cash_out': cash_out,
        'order_count': order_count,
        'active_order_count': active_orders.count(),
        'average_check': average_check,
        'payment_rows': payment_rows,
        'waiter_rows': waiter_rows,
        'top_products': top_products,
        'most_wasted_products': most_wasted_products,
        'low_stock_count': Product.objects.filter(quantity__lte=10).count(),
        'low_stock_rows': low_stock_rows,
        'open_shift_count': open_shifts.count(),
        'closed_shift_count': closed_shift_count,
        'table_status_rows': table_status_rows,
        'kitchen_status_rows': kitchen_status_rows,
        'busiest_table_rows': busiest_table_rows,
        'sales_chart': sales_chart,
        'payment_chart': payment_chart,
        'hourly_chart': hourly_chart,
        'waiter_chart': waiter_chart,
        'top_product_chart': top_product_chart,
    }

    return render(request, 'analytics/dashboard.html', context)
