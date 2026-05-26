from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


# =====================================
# AUTH
# =====================================

from authentication.views import (
    login_view,
    logout_view
)

from settingsapp.views import (
    admin_studio,
    accounting_dashboard,
    export_sales_excel,
    enterprise_dashboard,
    send_telegram_report_now,
    settings_dashboard,
    menu_management,
    staff_management,
    toggle_menu_item_availability
)


# =====================================
# ANALYTICS
# =====================================

from analyticsengine.views import (
    analytics_dashboard
)


# =====================================
# ORDERS
# =====================================

from orders.views import (
    table_list,
    create_order,
    order_detail,
    add_to_order,
    add_combo_to_order,
    update_order_workflow,
    update_order_item,
    adjust_order_item_quantity,
    hold_order,
    recall_order,
    transfer_order,
    merge_orders,
    split_order,
    repeat_last_order,
    void_order,
    refund_order
)


# =====================================
# WAITER
# =====================================

from waiter.views import (
    waiter_tables,
    waiter_pos,
    remove_order_item,
    send_to_kitchen,
    call_waiter
)


# =====================================
# KITCHEN
# =====================================

from kitchen.views import (
    kitchen_dashboard,
    update_order_status
)


# =====================================
# CASHIER
# =====================================

from cashier.views import (
    cashier_dashboard,
    generate_bill,
    refund_order_item
)


# =====================================
# DISPLAY
# =====================================

from display.views import (
    customer_display
)

from qrmenu.views import (
    qr_generator,
    qr_code_image,
    qr_menu,
    customer_order
)


# =====================================
# INVENTORY
# =====================================

from inventory.views import (
    inventory_dashboard,
    receive_purchase
)


# =====================================
# ROOT REDIRECT
# =====================================

def root_redirect(request):

    return redirect('/login/')


# =====================================
# URL PATTERNS
# =====================================

urlpatterns = [

    # ROOT

    path(
        '',
        root_redirect,
        name='root'
    ),


    # AUTH

    path(
        'login/',
        login_view,
        name='login'
    ),

    path(
        'logout/',
        logout_view,
        name='logout'
    ),


    # ADMIN

    path(
        'admin/',
        admin.site.urls
    ),


    # ANALYTICS

    path(
        'analytics/',
        analytics_dashboard,
        name='dashboard'
    ),


    # TABLES

    path(
        'tables/',
        table_list,
        name='tables'
    ),

    path(
        'create-order/<int:table_id>/',
        create_order,
        name='create_order'
    ),

    path(
        'order/<int:order_id>/',
        order_detail,
        name='order_detail'
    ),

    path(
        'add-to-order/<int:order_id>/<int:item_id>/',
        add_to_order,
        name='add_to_order'
    ),

    path(
        'add-combo-to-order/<int:order_id>/<int:combo_id>/',
        add_combo_to_order,
        name='add_combo_to_order'
    ),

    path(
        'order/<int:order_id>/workflow/',
        update_order_workflow,
        name='update_order_workflow'
    ),

    path(
        'order-item/<int:item_id>/update/',
        update_order_item,
        name='update_order_item'
    ),

    path(
        'order-item/<int:item_id>/<str:action>/',
        adjust_order_item_quantity,
        name='adjust_order_item_quantity'
    ),

    path(
        'order/<int:order_id>/hold/',
        hold_order,
        name='hold_order'
    ),

    path(
        'order/<int:order_id>/recall/',
        recall_order,
        name='recall_order'
    ),

    path(
        'order/<int:order_id>/transfer/',
        transfer_order,
        name='transfer_order'
    ),

    path(
        'order/<int:order_id>/merge/',
        merge_orders,
        name='merge_orders'
    ),

    path(
        'order/<int:order_id>/split/',
        split_order,
        name='split_order'
    ),

    path(
        'table/<int:table_id>/repeat-last/',
        repeat_last_order,
        name='repeat_last_order'
    ),

    path(
        'order/<int:order_id>/void/',
        void_order,
        name='void_order'
    ),

    path(
        'order/<int:order_id>/refund/',
        refund_order,
        name='refund_order'
    ),


    # WAITER

    path(
        'waiter/',
        waiter_tables,
        name='waiter_tables'
    ),

    path(
        'waiter/<int:table_id>/',
        waiter_pos,
        name='waiter_pos'
    ),

    path(
        'waiter/remove/<int:item_id>/',
        remove_order_item,
        name='remove_order_item'
    ),

    path(
        'waiter/send/<int:order_id>/',
        send_to_kitchen,
        name='send_to_kitchen'
    ),

    path(
        'call-waiter/<int:table_id>/',
        call_waiter,
        name='call_waiter'
    ),


    # KITCHEN

    path(
        'kitchen/',
        kitchen_dashboard,
        name='kitchen_dashboard'
    ),

    path(
        'update-order/<int:order_id>/<str:status>/',
        update_order_status,
        name='update_order_status'
    ),


    # CASHIER

    path(
        'cashier/',
        cashier_dashboard,
        name='cashier_dashboard'
    ),

    path(
        'bill/<int:order_id>/',
        generate_bill,
        name='generate_bill'
    ),

    path(
        'bill/<int:order_id>/item/<int:item_id>/refund/',
        refund_order_item,
        name='refund_order_item'
    ),


    # POS

    path(
        'pos/',
        include('pos.urls')
    ),

    path(
        'shifts/',
        include('shifts.urls')
    ),

    path(
        'floor/',
        include('floorplan.urls')
    ),


    # DISPLAY

    path(
        'display/',
        customer_display,
        name='customer_display'
    ),


    # QR MENU

    path(
        'qr/',
        qr_generator,
        name='qr_generator'
    ),

    path(
        'qr/<int:table_id>/image/',
        qr_code_image,
        name='qr_code_image'
    ),

    path(
        'qr-menu/<int:table_id>/',
        qr_menu,
        name='qr_menu'
    ),

    path(
        'qr-menu/<int:table_id>/order/<int:item_id>/',
        customer_order,
        name='customer_order'
    ),


    # INVENTORY

    path(
        'inventory-dashboard/',
        inventory_dashboard,
        name='inventory_dashboard'
    ),

    path(
        'inventory/purchase/<int:purchase_id>/receive/',
        receive_purchase,
        name='receive_purchase'
    ),

    path(
        'settings/',
        settings_dashboard,
        name='settings_dashboard'
    ),

    path(
        'settings/studio/',
        admin_studio,
        name='admin_studio'
    ),

    path(
        'enterprise/',
        enterprise_dashboard,
        name='enterprise_dashboard'
    ),

    path(
        'accounting/',
        accounting_dashboard,
        name='accounting_dashboard'
    ),

    path(
        'settings/menu/',
        menu_management,
        name='menu_management'
    ),

    path(
        'settings/menu/<int:item_id>/toggle/',
        toggle_menu_item_availability,
        name='toggle_menu_item_availability'
    ),

    path(
        'settings/staff/',
        staff_management,
        name='staff_management'
    ),

    path(
        'reports/sales.xlsx',
        export_sales_excel,
        name='export_sales_excel'
    ),

    path(
        'reports/telegram/send/',
        send_telegram_report_now,
        name='send_telegram_report_now'
    ),

]


# =====================================
# STATIC / MEDIA
# =====================================

if settings.DEBUG:

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
