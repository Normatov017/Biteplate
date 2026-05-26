from decimal import Decimal


# =====================================
# BASE STRATEGY
# =====================================

class PricingStrategy:

    def calculate_total(

        self,
        subtotal

    ):

        raise NotImplementedError(


            'Subclasses must implement '

            'calculate_total()'

        )


# =====================================
# STANDARD PRICING
# =====================================

class StandardPricing(

    PricingStrategy

):

    def calculate_total(

        self,
        subtotal

    ):

        return subtotal


# =====================================
# HAPPY HOUR
# =====================================

class HappyHourPricing(

    PricingStrategy

):

    def calculate_total(

        self,
        subtotal

    ):

        discount = (

            subtotal *

            Decimal('0.20')

        )

        return subtotal - discount


# =====================================
# WEEKEND PRICING
# =====================================

class WeekendPricing(

    PricingStrategy

):

    def calculate_total(

        self,
        subtotal

    ):

        surcharge = (

            subtotal *

            Decimal('0.10')

        )

        return subtotal + surcharge


# =====================================
# VIP PRICING
# =====================================

class VIPPricing(

    PricingStrategy

):

    def calculate_total(

        self,
        subtotal

    ):

        discount = (

            subtotal *

            Decimal('0.15')

        )

        return subtotal - discount