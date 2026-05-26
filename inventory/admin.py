from django.contrib import admin

from .models import Product
from .models import RecipeIngredient
from .models import Supplier
from .models import Purchase
from .models import PurchaseItem


# =========================
# PURCHASE ITEM INLINE
# =========================

class PurchaseItemInline(admin.TabularInline):

    model = PurchaseItem

    extra = 1


# =========================
# PURCHASE ADMIN
# =========================

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):

    list_display = (

        'invoice_number',

        'restaurant',

        'branch',

        'supplier',

        'status',

        'total_amount',

        'created_at',

    )

    list_filter = (

        'restaurant',

        'branch',

        'supplier',

        'status',

    )

    search_fields = (

        'invoice_number',

        'supplier__name',

    )

    inlines = [

        PurchaseItemInline

    ]

    actions = [

        'mark_as_received'

    ]


    def mark_as_received(

        self,

        request,

        queryset

    ):

        for purchase in queryset:

            purchase.receive_products()


    mark_as_received.short_description = (

        'Receive selected purchases'

    )


# =========================
# OTHER MODELS
# =========================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'restaurant',
        'branch',
        'quantity',
        'minimum_quantity',
        'unit',
        'cost_price',
    )

    list_filter = (
        'restaurant',
        'branch',
        'unit',
    )

    search_fields = (
        'name',
        'barcode',
        'supplier_code',
    )

admin.site.register(RecipeIngredient)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'restaurant',
        'branch',
        'phone',
        'email',
    )

    list_filter = (
        'restaurant',
        'branch',
    )

    search_fields = (
        'name',
        'phone',
        'email',
    )
