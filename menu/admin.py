from django.contrib import admin

from .models import (
    MenuItem,
    ModifierGroup,
    ModifierOption,
    ProductVariant,
    ComboMeal,
    SingleMenuItem
)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'category',
        'price',
        'available',
        'available_from',
        'available_to',
        'branch',
    )

    list_filter = (
        'available',
        'category',
        'branch',
    )

    search_fields = (
        'name',
        'description',
    )

admin.site.register(ComboMeal)

admin.site.register(SingleMenuItem)

admin.site.register(ModifierGroup)

admin.site.register(ModifierOption)
