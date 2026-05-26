from django.shortcuts import render

from orders.models import Order


def customer_display(request):

    preparing_orders = Order.objects.filter(
        kitchen_status__in=[
            'waiting',
            'preparing',
        ],
        is_paid=False,
    ).order_by(
        '-created_at'
    )

    ready_orders = Order.objects.filter(
        kitchen_status='ready',
        is_paid=False,
    ).order_by(
        '-created_at'
    )

    context = {
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
    }

    return render(
        request,
        'display.html',
        context
    )
