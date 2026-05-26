from django.contrib import admin

from .models import (
    Table,
    Order,
    OrderItem,
    OrderItemModifier
)


# =========================
# ORDER ITEM INLINE
# =========================

class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0

    readonly_fields = [

        'created_at'

    ]


# =========================
# TABLE ADMIN
# =========================

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):

    list_display = [

        'table_number',

        'status',

        'seats',

        'assigned_waiter',

        'is_active',

    ]

    list_filter = [

        'status',

        'is_active',

    ]

    search_fields = [

        'table_number',

        'assigned_waiter',

    ]


# =========================
# ORDER ADMIN
# =========================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = [

        'id',

        'table',

        'status',

        'kitchen_status',

        'payment_method',

        'is_paid',

        'total_amount',

        'priority',

        'created_at',

    ]

    list_filter = [

        'status',

        'kitchen_status',

        'payment_method',

        'is_paid',

    ]

    search_fields = [

        'id',

        'customer_name',

        'customer_phone',

    ]

    readonly_fields = [

        'created_at',

        'updated_at',

        'started_at',

        'ready_at',

    ]

    inlines = [

        OrderItemInline

    ]

    fieldsets = (

        (

            'Order Information',

            {

                'fields': (

                    'table',

                    'order_type',

                    'status',

                    'kitchen_status',

                )

            }

        ),

        (

            'Customer',

            {

                'fields': (

                    'customer_name',

                    'customer_phone',

                )

            }

        ),

        (

            'Payment',

            {

                'fields': (

                    'payment_method',

                    'is_paid',

                    'total_amount',

                )

            }

        ),

        (

            'Kitchen',

            {

                'fields': (

                    'priority',

                    'estimated_time',

                    'started_at',

                    'ready_at',

                )

            }

        ),

        (

            'Merge',

            {

                'fields': (

                    'is_merged',

                    'merged_into',

                )

            }

        ),

        (

            'Extra',

            {

                'fields': (

                    'notes',

                    'created_at',

                    'updated_at',

                )

            }

        ),

    )


# =========================
# ORDER ITEM ADMIN
# =========================

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = [

        'id',

        'order',

        'menu_item',

        'quantity',

        'created_at',

    ]

    list_filter = [

        'created_at',

    ]

    search_fields = [

        'menu_item__name',

    ]


# =========================
# MODIFIER ADMIN
# =========================

@admin.register(OrderItemModifier)
class OrderItemModifierAdmin(admin.ModelAdmin):

    list_display = [

        'id',

        'order_item',

        'modifier_option',

        'extra_price',

    ]

    search_fields = [

        'modifier_option__name',

    ]