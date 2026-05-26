from decimal import Decimal

from .models import (
    RecipeIngredient,
    StockMovement,
    InventoryConsumption
)


# =====================================
# INVENTORY SERVICE
# =====================================

class InventoryService:


    # =====================================
    # AUTO DEDUCT INVENTORY
    # =====================================

    @staticmethod
    def deduct_order_inventory(

        order

    ):

        if order.inventory_consumptions.exists():

            return

        for item in order.items.all():

            recipes = RecipeIngredient.objects.filter(

                menu_item=item.menu_item

            )

            for recipe in recipes:

                total_quantity = (

                    Decimal(

                        str(

                            recipe.quantity_required

                        )

                    )

                    *

                    Decimal(

                        str(item.quantity)

                    )

                )

                product = recipe.product

                before_qty = product.quantity

                product.quantity -= float(

                    total_quantity

                )

                product.save()


                # =====================================
                # STOCK MOVEMENT
                # =====================================

                StockMovement.objects.create(

                    product=product,

                    movement_type='auto_deduction',

                    quantity=float(

                        total_quantity

                    ),

                    before_quantity=before_qty,

                    after_quantity=product.quantity,

                    note=(

                        f'Auto deduction '

                        f'for Order '

                        f'#{order.id}'

                    )

                )


                # =====================================
                # INVENTORY CONSUMPTION
                # =====================================

                InventoryConsumption.objects.create(

                    order=order,

                    product=product,

                    quantity_used=float(

                        total_quantity

                    )

                )
