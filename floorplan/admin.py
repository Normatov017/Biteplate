from django.contrib import admin

from .models import FloorDecor


@admin.register(FloorDecor)
class FloorDecorAdmin(admin.ModelAdmin):

    list_display = (
        'label',
        'decor_type',
        'floor_area',
        'branch',
    )

    list_filter = (
        'decor_type',
        'floor_area',
        'branch',
    )
