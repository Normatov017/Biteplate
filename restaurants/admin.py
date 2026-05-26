from django.contrib import admin

from .models import Restaurant
from .models import Branch


class BranchInline(admin.TabularInline):

    model = Branch

    extra = 1


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'slug',
        'currency',
        'timezone',
        'active',
    )

    search_fields = (
        'name',
        'slug',
        'phone',
    )

    list_filter = (
        'active',
        'currency',
    )

    inlines = [
        BranchInline
    ]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'restaurant',
        'phone',
        'active',
    )

    list_filter = (
        'restaurant',
        'active',
    )

    search_fields = (
        'name',
        'restaurant__name',
        'phone',
    )
