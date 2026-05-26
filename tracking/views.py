from django.shortcuts import render
from django.shortcuts import get_object_or_404

from orders.models import Order


def track_order(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    context = {

        'order': order

    }

    return render(
        request,
        'tracking/track_order.html',
        context
    )   