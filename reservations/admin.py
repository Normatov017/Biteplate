from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):

    list_display = (
        'customer_name',
        'table',
        'reservation_time',
        'end_time',
        'guest_count',
        'status',
    )

    list_filter = (
        'status',
        'reservation_time',
        'table',
    )

    search_fields = (
        'customer_name',
        'phone_number',
    )
