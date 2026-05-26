from django.urls import path

from .views import (
    pos_terminal,
    open_table_register,
    mark_table_free,
    add_to_order_cart,
    add_combo_to_pos_order,
    apply_order_discount,
    adjust_order_cart_item,
    pos_orders,
    pos_reservations,
    open_reservation_order,
    send_reservation_reminders_now,
    add_to_cart,
    clear_cart,
    complete_payment,
    increase_quantity,
    decrease_quantity,
    hold_cart,
    payment_page,
    resume_held_order,
    cancel_held_order,
    waiter_pin_login,
    waiter_pin_logout,
    waiter_commission_dashboard,
)

urlpatterns = [

    path(
        '',
        pos_terminal,
        name='pos_terminal'
    ),

    path(
        'table/<int:table_id>/',
        open_table_register,
        name='open_table_register'
    ),

    path(
        'table/<int:table_id>/free/',
        mark_table_free,
        name='mark_table_free'
    ),

    path(
        'orders/',
        pos_orders,
        name='pos_orders'
    ),

    path(
        'waiter/login/',
        waiter_pin_login,
        name='waiter_pin_login'
    ),

    path(
        'waiter/logout/',
        waiter_pin_logout,
        name='waiter_pin_logout'
    ),

    path(
        'waiters/',
        waiter_commission_dashboard,
        name='waiter_commission_dashboard'
    ),

    path(
        'reservations/',
        pos_reservations,
        name='pos_reservations'
    ),

    path(
        'reservations/<int:reservation_id>/open/',
        open_reservation_order,
        name='open_reservation_order'
    ),

    path(
        'reservations/reminders/send/',
        send_reservation_reminders_now,
        name='send_reservation_reminders_now'
    ),

    path(
        'order/<int:order_id>/add/<int:product_id>/',
        add_to_order_cart,
        name='add_to_order_cart'
    ),

    path(
        'order/<int:order_id>/combo/<int:combo_id>/',
        add_combo_to_pos_order,
        name='add_combo_to_pos_order'
    ),

    path(
        'order/<int:order_id>/discount/',
        apply_order_discount,
        name='apply_order_discount'
    ),

    path(
        'order-item/<int:item_id>/<str:action>/',
        adjust_order_cart_item,
        name='adjust_order_cart_item'
    ),

    path(
        'add/<int:product_id>/',
        add_to_cart,
        name='add_to_cart'
    ),

    path(
        'clear/',
        clear_cart,
        name='clear_cart'
    ),

    path(
        'increase/<int:index>/',
        increase_quantity,
        name='increase_quantity'
    ),

    path(
        'decrease/<int:index>/',
        decrease_quantity,
        name='decrease_quantity'
    ),

    path(
        'payment/',
        payment_page,
        name='payment_page'
    ),

    path(
        'payment/<str:method>/',
        complete_payment,
        name='complete_payment'
    ),

    path(
        'hold/',
        hold_cart,
        name='hold_cart'
    ),

    path(
        'held/<int:held_order_id>/resume/',
        resume_held_order,
        name='resume_held_order'
    ),

    path(
        'held/<int:held_order_id>/cancel/',
        cancel_held_order,
        name='cancel_held_order'
    ),

]
