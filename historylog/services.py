# =====================================
# SINGLETON HISTORY LOGGER
# =====================================

class OrderHistoryLogger:


    _instance = None


    # =====================================
    # SINGLETON INSTANCE
    # =====================================

    def __new__(

        cls

    ):

        if cls._instance is None:

            cls._instance = super(

                OrderHistoryLogger,

                cls

            ).__new__(cls)

        return cls._instance


    # =====================================
    # LOG EVENT
    # =====================================

    def log(

        self,
        order,
        message

    ):

        from .models import (
            OrderHistoryLog
        )

        OrderHistoryLog.objects.create(

            order=order,

            message=message

        )


    def log_confirmed_order(
        self,
        order
    ):

        items = ', '.join(
            f'{item.menu_item.name} x{item.quantity}'
            for item in order.items.select_related('menu_item').all()
        )

        staff_id = (
            getattr(order.waiter, 'employee_id', None)
            or getattr(order.waiter, 'username', None)
            or 'system'
        )

        table_number = getattr(order.table, 'table_number', '-')

        message = (
            f'CONFIRMED | order={order.id} | table={table_number} | '
            f'staff={staff_id} | items={items or "-"} | '
            f'total={order.total_amount}'
        )

        self.log(order, message)


    def get_orders(
        self,
        date_from=None,
        date_to=None,
        table=None
    ):

        logs = self._confirmed_logs()

        if date_from:

            logs = logs.filter(
                created_at__date__gte=date_from
            )

        if date_to:

            logs = logs.filter(
                created_at__date__lte=date_to
            )

        if table is not None:

            logs = logs.filter(
                order__table=table
            )

        return logs.select_related(
            'order',
            'order__table',
            'order__waiter'
        ).order_by('-created_at')


    def get_orders_by_table(
        self,
        table
    ):

        return self.get_orders(
            table=table
        )


    def get_orders_in_date_range(
        self,
        date_from,
        date_to
    ):

        return self.get_orders(
            date_from=date_from,
            date_to=date_to
        )


    def get_most_frequent_item(
        self,
        date_from=None,
        date_to=None
    ):

        from django.db.models import Count

        from orders.models import OrderItem

        items = OrderItem.objects.filter(
            order__history_logs__message__startswith='CONFIRMED'
        )

        if date_from:

            items = items.filter(
                order__history_logs__created_at__date__gte=date_from
            )

        if date_to:

            items = items.filter(
                order__history_logs__created_at__date__lte=date_to
            )

        return items.values(
            'menu_item__name'
        ).annotate(
            total=Count('id')
        ).order_by(
            '-total',
            'menu_item__name'
        ).first()


    def _confirmed_logs(self):

        from .models import (
            OrderHistoryLog
        )

        return OrderHistoryLog.objects.filter(
            message__startswith='CONFIRMED'
        )
