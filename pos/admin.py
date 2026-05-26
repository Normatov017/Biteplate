from django.contrib import admin

from .models import HeldOrder


@admin.register(HeldOrder)
class HeldOrderAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'cashier',
        'total',
        'status',
        'created_at',
        'resumed_at',
    ]

    list_filter = [
        'status',
        'created_at',
    ]

    search_fields = [
        'note',
        'cashier__username',
    ]

