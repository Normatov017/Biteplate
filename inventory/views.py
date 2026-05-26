from decimal import Decimal

from django.db import models

from django.db.models import (
    Sum,
    Count
)

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .models import (
    Product,
    Purchase,
    StockMovement,
    InventoryWaste,
    Supplier
)

from menu.models import MenuItem

from orders.models import OrderItem

from billing.models import Payment

from permissionsapp.utils import permission_required


# =====================================
# INVENTORY DASHBOARD
# =====================================

@permission_required(
    'inventory',
    'view'
)
def inventory_dashboard(request):

    # =====================================
    # LOW STOCK PRODUCTS
    # =====================================

    low_stock_items = Product.objects.filter(

        quantity__lte=models.F('minimum_quantity')

    ).order_by(

        'quantity'

    )


    # =====================================
    # TOTAL INVENTORY VALUE
    # =====================================

    inventory_value = Decimal('0')

    products = Product.objects.all()

    for product in products:

        inventory_value += (

            Decimal(str(product.quantity))

            *

            product.cost_price

        )


    # =====================================
    # TOTAL PRODUCTS
    # =====================================

    total_products = Product.objects.count()


    # =====================================
    # TOTAL STOCK QUANTITY
    # =====================================

    total_stock_quantity = Product.objects.aggregate(

        total=Sum('quantity')

    )['total'] or 0


    # =====================================
    # MOST WASTED PRODUCTS
    # =====================================

    most_wasted = (

        InventoryWaste.objects.values(

            'product__name'

        ).annotate(

            total_waste=Sum('quantity')

        ).order_by(

            '-total_waste'

        )[:5]

    )


    # =====================================
    # PURCHASE ANALYTICS
    # =====================================

    total_purchases = Purchase.objects.count()

    received_purchases = Purchase.objects.filter(

        status='received'

    ).count()

    pending_purchases = Purchase.objects.filter(

        status='draft'

    ).count()

    purchase_total = Purchase.objects.aggregate(

        total=Sum('total_amount')

    )['total'] or Decimal('0')


    # =====================================
    # STOCK MOVEMENTS
    # =====================================

    stock_movements = (

        StockMovement.objects.order_by(

            '-created_at'

        )[:10]

    )


    # =====================================
    # MENU PROFIT ANALYTICS
    # =====================================

    menu_profit_data = []

    menu_items = MenuItem.objects.all()

    for item in menu_items:

        ingredient_cost = Decimal('0')

        try:

            for recipe in item.recipe_items.all():

                ingredient_cost += (

                    Decimal(

                        str(recipe.quantity_required)

                    )

                    *

                    recipe.product.cost_price

                )

        except:

            pass


        profit = (

            Decimal(str(item.price))

            -

            ingredient_cost

        )

        margin = 0

        if item.price > 0:

            margin = (

                profit / Decimal(str(item.price))

            ) * 100


        menu_profit_data.append({

            'name': item.name,

            'price': round(
                item.price,
                2
            ),

            'cost': round(
                ingredient_cost,
                2
            ),

            'profit': round(
                profit,
                2
            ),

            'margin': round(
                margin,
                2
            )

        })


    # =====================================
    # TOP SELLING PRODUCTS
    # =====================================

    top_products = (

        OrderItem.objects.values(

            'menu_item__name'

        ).annotate(

            total_sold=Sum('quantity')

        ).order_by(

            '-total_sold'

        )[:5]

    )


    # =====================================
    # TOTAL PAYMENTS
    # =====================================

    total_revenue = Payment.objects.filter(

        status='paid'

    ).aggregate(

        total=Sum('amount')

    )['total'] or Decimal('0')


    # =====================================
    # RECENT PURCHASES
    # =====================================

    recent_purchases = Purchase.objects.order_by(

        '-created_at'

    )[:5]


    # =====================================
    # CONTEXT
    # =====================================

    context = {

        'low_stock_items': low_stock_items,

        'low_stock_products': low_stock_items,

        'inventory_value': round(
            inventory_value,
            2
        ),

        'total_products': total_products,

        'total_stock_quantity': total_stock_quantity,

        'most_wasted': most_wasted,

        'total_purchases': total_purchases,

        'purchases': total_purchases,

        'received_purchases': received_purchases,

        'received': received_purchases,

        'pending_purchases': pending_purchases,

        'purchase_total': round(
            purchase_total,
            2
        ),

        'stock_movements': stock_movements,

        'menu_profit_data': menu_profit_data,

        'top_products': top_products,

        'total_revenue': round(
            total_revenue,
            2
        ),

        'recent_purchases': recent_purchases,

        'low_stock': low_stock_items.count(),

        'wasted_products': most_wasted,

        'products': products.order_by('name'),

        'suppliers': Supplier.objects.order_by('name'),

    }

    return render(

        request,

        'inventory/inventory_dashboard.html',

        context

    )


@permission_required(
    'inventory',
    'edit'
)
def receive_purchase(request, purchase_id):

    purchase = get_object_or_404(
        Purchase,
        id=purchase_id
    )

    purchase.receive_products()

    messages.success(
        request,
        f'Purchase {purchase.invoice_number} received.'
    )

    next_url = request.GET.get('next') or request.POST.get('next')

    if next_url:

        return redirect(next_url)

    return redirect(
        'inventory_dashboard'
    )
