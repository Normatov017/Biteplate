from django.contrib import admin

from .models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):

    list_display = (
        'restaurant',
        'branch',
        'currency',
        'tax_percent',
        'service_fee_percent',
        'auto_print_receipt',
        'auto_inventory_deduction',
    )

    list_filter = (
        'restaurant',
        'branch',
        'currency',
        'language',
    )

    search_fields = (
        'restaurant__name',
        'branch__name',
    )
