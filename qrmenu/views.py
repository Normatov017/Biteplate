from django.shortcuts import (
    render,
    get_object_or_404,
    redirect
)
from django.http import HttpResponse
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone

import qrcode
from io import BytesIO

from realtime.utils import (
    send_order_update
)

from orders.models import (
    Table,
    Order,
    OrderItem
)

from menu.models import MenuItem


# =========================
# QR GENERATOR DASHBOARD
# =========================

def qr_generator(request):

    tables = Table.objects.filter(
        is_active=True
    ).exclude(
        table_number=0
    ).order_by(
        'table_number'
    )

    context = {

        'tables': tables,

    }

    return render(

        request,

        'qrmenu/generator.html',

        context

    )


# =========================
# QR IMAGE
# =========================

def qr_code_image(

    request,

    table_id

):

    table = get_object_or_404(

        Table,

        id=table_id

    )

    menu_path = reverse(

        'qr_menu',

        args=[
            table.id
        ]

    )

    menu_url = request.build_absolute_uri(

        menu_path

    )

    qr = qrcode.QRCode(

        version=1,

        box_size=10,

        border=2

    )

    qr.add_data(

        menu_url

    )

    qr.make(

        fit=True

    )

    image = qr.make_image(

        fill_color='black',

        back_color='white'

    )

    buffer = BytesIO()

    image.save(

        buffer,

        format='PNG'

    )

    return HttpResponse(

        buffer.getvalue(),

        content_type='image/png'

    )


# =========================
# QR MENU PAGE
# =========================

def qr_menu(

    request,

    table_id

):

    table = get_object_or_404(

        Table,

        id=table_id

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
    )

    context = {

        'table': table,

        'menu_items': menu_items,

    }

    return render(

        request,

        'qr_menu.html',

        context

    )


# =========================
# CUSTOMER PLACE ORDER
# =========================

def customer_order(

    request,

    table_id,

    item_id

):

    table = get_object_or_404(

        Table,

        id=table_id

    )

    menu_item = get_object_or_404(

        MenuItem,

        id=item_id

    )

    order = Order.objects.filter(
        table=table,
        is_paid=False,
        status__in=[
            'pending',
            'held',
            'preparing',
            'ready',
            'served',
        ]
    ).order_by(
        '-created_at'
    ).first()

    if not order:

        order = Order.objects.create(

            table=table,

            status='pending',

            kitchen_status='waiting',

            order_type='dine_in',

            notes='Created from QR menu'

        )

    OrderItem.objects.create(

        order=order,

        menu_item=menu_item,

        quantity=1

    )

    table.status = 'occupied'

    table.save()


    # =========================
    # REALTIME EVENT
    # =========================

    try:

        send_order_update(

            {

                'type': 'customer_order',

                'table': table.table_number,

                'order_id': order.id,

                'item': menu_item.name,

                'message': (

                    f'Table '

                    f'{table.table_number} '

                    f'ordered '

                    f'{menu_item.name}'

                )

            }

        )

    except Exception as e:

        print(

            'Realtime Error:',

            str(e)

        )


    return redirect(

        'qr_menu',

        table_id=table.id

    )   
