from django.contrib import admin

from .models import Shift, ShiftLog, CashMovement


# =========================
# SHIFT ADMIN
# =========================

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):

    list_display = (

        'id',

        'cashier',

        'status',

        'opening_cash',

        'closing_cash',

        'expected_cash',

        'difference',

        'opened_at',

    )

    list_filter = (

        'status',

        'opened_at',

    )

    search_fields = (

        'cashier__username',

    )


@admin.register(ShiftLog)
class ShiftLogAdmin(admin.ModelAdmin):

    list_display = (
        'employee',
        'clock_in',
        'clock_out',
        'note',
    )

    list_filter = (
        'clock_in',
        'clock_out',
    )

    search_fields = (
        'employee__username',
        'employee__first_name',
        'employee__last_name',
    )


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):

    list_display = (
        'shift',
        'movement_type',
        'amount',
        'reason',
        'created_by',
        'created_at',
    )

    list_filter = (
        'movement_type',
        'created_at',
    )
