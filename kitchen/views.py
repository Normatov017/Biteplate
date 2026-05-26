from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404

from django.utils import timezone

from orders.models import Order
from orders.models import OrderItem

from realtime.utils import send_order_update

from accounts.permissions import role_required

from permissionsapp.utils import (
    permission_required
)

from commandengine.commands import (
    PrepareOrderCommand,
    ReadyOrderCommand,
    CancelOrderCommand
)

from commandengine.services import (
    KitchenQueue
)

from observerengine.subject import (
    OrderSubject
)

from observerengine.observers import (
    WaiterObserver,
    ManagerObserver,
    KitchenObserver
)

from historylog.services import (
    OrderHistoryLogger
)


# =====================================
# KITCHEN DASHBOARD
# =====================================

@role_required([
    'kitchen',
    'manager',
    'owner',
    'super_admin'
])
@permission_required(
    'kitchen',
    'view'
)
def kitchen_dashboard(request):

    # =====================================
    # ACTIVE ORDERS
    # =====================================

    orders = list(Order.objects.exclude(

        kitchen_status__in=[
            'served',
            'cancelled'
        ]

    ).prefetch_related(

        'items__menu_item',
        'items__modifiers__modifier_option',

    ).order_by(

        '-priority',

        'created_at'

    ))

    for order in orders:

        order.kitchen_items = [
            item
            for item in order.items.all()
            if item.kitchen_status in [
                'waiting',
                'preparing',
                'ready'
            ]
        ]

    orders = [
        order
        for order in orders
        if order.kitchen_items
    ]


    # =====================================
    # COUNTS
    # =====================================

    waiting_count = len([
        order
        for order in orders
        if order.kitchen_status == 'waiting'
    ])

    preparing_count = len([
        order
        for order in orders
        if order.kitchen_status == 'preparing'
    ])

    ready_count = len([
        order
        for order in orders
        if order.kitchen_status == 'ready'
    ])

    served_count = Order.objects.filter(

        kitchen_status='served'

    ).count()

    cancelled_count = Order.objects.filter(

        kitchen_status='cancelled'

    ).count()


    # =====================================
    # CONTEXT
    # =====================================

    context = {

        'orders': orders,

        'waiting_count': waiting_count,

        'preparing_count': preparing_count,

        'ready_count': ready_count,

        'served_count': served_count,

        'cancelled_count': cancelled_count,

    }

    return render(

        request,

        'kitchen/dashboard.html',

        context

    )


# =====================================
# UPDATE ORDER STATUS
# =====================================

@role_required([
    'kitchen',
    'manager',
    'owner',
    'super_admin'
])
@permission_required(
    'kitchen',
    'edit'
)
def update_order_status(

    request,

    order_id,

    status

):

    order = get_object_or_404(

        Order,

        id=order_id

    )


    # =====================================
    # COMMAND QUEUE
    # =====================================

    queue = KitchenQueue()


    # =====================================
    # PREPARING
    # =====================================

    if status == 'preparing':

        command = PrepareOrderCommand(
            order
        )

        queue.run(command)

        order.kitchen_status = 'preparing'

        order.started_at = timezone.now()
        order.items.exclude(
            kitchen_status__in=[
                'served',
                'cancelled'
            ]
        ).update(
            kitchen_status='preparing'
        )


    # =====================================
    # READY
    # =====================================

    elif status == 'ready':

        command = ReadyOrderCommand(
            order
        )

        queue.run(command)

        order.kitchen_status = 'ready'

        order.ready_at = timezone.now()
        order.items.exclude(
            kitchen_status__in=[
                'served',
                'cancelled'
            ]
        ).update(
            kitchen_status='ready'
        )


    # =====================================
    # CANCELLED
    # =====================================

    elif status == 'cancelled':

        command = CancelOrderCommand(
            order
        )

        queue.run(command)

        order.kitchen_status = 'cancelled'
        order.items.exclude(
            kitchen_status='served'
        ).update(
            kitchen_status='cancelled'
        )


    # =====================================
    # SERVED
    # =====================================

    elif status == 'served':

        order.kitchen_status = 'served'

        order.status = 'served'
        order.items.exclude(
            kitchen_status__in=[
                'served',
                'cancelled'
            ]
        ).update(
            kitchen_status='served'
        )


    # =====================================
    # SAVE
    # =====================================

    order.save()


    # =====================================
    # SINGLETON HISTORY LOGGER
    # =====================================

    logger = OrderHistoryLogger()

    logger.log(

        order,

        f'Kitchen status changed to {status}'

    )


    # =====================================
    # OBSERVER PATTERN
    # =====================================

    subject = OrderSubject()

    subject.register(
        WaiterObserver()
    )

    subject.register(
        ManagerObserver()
    )

    subject.register(
        KitchenObserver()
    )

    subject.notify({

        'order_id': order.id,

        'table': order.table.table_number,

        'status': status,

    })


    # =====================================
    # REALTIME EVENT
    # =====================================

    try:

        send_order_update(

            {

                'type': 'kitchen_update',

                'order_id': order.id,

                'table': order.table.table_number,

                'status': status,

                'message': (

                    f'Order #{order.id} '

                    f'updated to '

                    f'{status}'

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
