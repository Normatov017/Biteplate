from celery import shared_task

from .models import Product


# =========================
# LOW STOCK CHECK
# =========================

@shared_task
def check_low_stock():

    low_stock_products = []

    products = Product.objects.all()

    for product in products:

        if product.is_low_stock():

            low_stock_products.append(

                product.name

            )

    print(

        'LOW STOCK:',

        low_stock_products

    )

    return low_stock_products