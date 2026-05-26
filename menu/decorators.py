from decimal import Decimal


# =====================================
# BASE PRODUCT
# =====================================

class BaseProduct:

    def __init__(

        self,
        menu_item

    ):

        self.menu_item = menu_item

    def get_name(self):

        return self.menu_item.name

    def get_price(self):

        return Decimal(

            str(

                self.menu_item.price

            )

        )


# =====================================
# PRODUCT DECORATOR
# =====================================

class ProductDecorator:

    def __init__(

        self,
        product

    ):

        self.product = product

    def get_name(self):

        return self.product.get_name()

    def get_price(self):

        return self.product.get_price()


# =====================================
# EXTRA CHEESE
# =====================================

class ExtraCheeseDecorator(

    ProductDecorator

):

    def get_name(self):

        return (

            f'{self.product.get_name()} '

            f'+ Extra Cheese'

        )

    def get_price(self):

        return (

            self.product.get_price()

            + Decimal('2')

        )


# =====================================
# DOUBLE MEAT
# =====================================

class DoubleMeatDecorator(

    ProductDecorator

):

    def get_name(self):

        return (

            f'{self.product.get_name()} '

            f'+ Double Meat'

        )

    def get_price(self):

        return (

            self.product.get_price()

            + Decimal('5')

        )


# =====================================
# LARGE SIZE
# =====================================

class LargeSizeDecorator(

    ProductDecorator

):

    def get_name(self):

        return (

            f'{self.product.get_name()} '

            f'+ Large Size'

        )

    def get_price(self):

        return (

            self.product.get_price()

            + Decimal('3')

        )


# =====================================
# SPICY SAUCE
# =====================================

class SpicySauceDecorator(

    ProductDecorator

):

    def get_name(self):

        return (

            f'{self.product.get_name()} '

            f'+ Spicy Sauce'

        )

    def get_price(self):

        return (

            self.product.get_price()

            + Decimal('1')

        )