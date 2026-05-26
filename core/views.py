from decimal import Decimal

from django.db.models import (
    Count,
    Sum
)

from django.shortcuts import render

from billing.models import Payment

from inventory.models import Product

from orders.models import (
    Order,
    OrderItem,
    Table
)

from menu.models import MenuItem


def dashboard(request):

    # =========================
    # MAIN STATS
    # =========================

    total_orders = Order.objects.count()

    active_tables = Table.objects.filter(
        status='occupied'
    ).count()

    total_tables = Table.objects.count()


    # =========================
    # PAID / UNPAID
    # =========================

    paid_orders = Order.objects.filter(
        is_paid=True
    ).count()

    unpaid_orders = Order.objects.filter(
        is_paid=False
    ).count()


    # =========================
    # REVENUE
    # =========================

    revenue = Decimal('0')

    paid_items = OrderItem.objects.filter(
        order__is_paid=True
    )

    for item in paid_items:

        revenue += item.get_total()


    # =========================
    # AVERAGE ORDER VALUE
    # =========================

    avg_order_value = 0

    if paid_orders > 0:

        avg_order_value = (

            revenue / paid_orders

        )


    # =========================
    # TOP SELLING ITEMS
    # =========================

    top_items = (

        OrderItem.objects.values(

            'menu_item__name'

        ).annotate(

            total_qty=Sum('quantity')

        ).order_by(

            '-total_qty'

        )[:5]

    )


    # =========================
    # PAYMENT ANALYTICS
    # =========================

    cash_payments = Payment.objects.filter(
        method='cash',
        status='paid'
    ).count()

    card_payments = Payment.objects.filter(
        method='card',
        status='paid'
    ).count()

    click_payments = Payment.objects.filter(
        method='click',
        status='paid'
    ).count()

    payme_payments = Payment.objects.filter(
        method='payme',
        status='paid'
    ).count()


    # =========================
    # LOW STOCK
    # =========================

    low_stock_products = Product.objects.filter(

        quantity__lte=10

    )[:5]


    # =========================
    # LIVE ACTIVITIES
    # =========================

    latest_orders = Order.objects.order_by(
        '-created_at'
    )[:10]

    activities = []

    for order in latest_orders:

        activities.append({

            'title': f'Order #{order.id}',

            'description': (

                f'Table '

                f'{order.table.table_number} '

                f'created a new order'

            ),

            'status': order.status

        })


    # =========================
    # KITCHEN STATS
    # =========================

    pending_orders = Order.objects.filter(
        kitchen_status='waiting'
    ).count()

    preparing_orders = Order.objects.filter(
        kitchen_status='preparing'
    ).count()

    ready_orders = Order.objects.filter(
        kitchen_status='ready'
    ).count()

    served_orders = Order.objects.filter(
        status='served'
    ).count()

    cancelled_orders = Order.objects.filter(
        status='cancelled'
    ).count()


    # =========================
    # CONTEXT
    # =========================

    context = {

        'revenue': revenue,

        'total_orders': total_orders,

        'active_tables': active_tables,

        'total_tables': total_tables,

        'paid_orders': paid_orders,

        'unpaid_orders': unpaid_orders,

        'avg_order_value': round(
            avg_order_value,
            2
        ),

        'top_items': top_items,

        'activities': activities,

        'pending_orders': pending_orders,

        'preparing_orders': preparing_orders,

        'ready_orders': ready_orders,

        'served_orders': served_orders,

        'cancelled_orders': cancelled_orders,

        'cash_payments': cash_payments,

        'card_payments': card_payments,

        'click_payments': click_payments,

        'payme_payments': payme_payments,

        'low_stock_products': low_stock_products,

    }

    return render(

        request,

        'dashboard.html',

        context

    )