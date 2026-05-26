from .strategies import (
    StandardPricing,
    HappyHourPricing,
    WeekendPricing,
    VIPPricing
)


# =====================================
# PRICING SERVICE
# =====================================

class PricingService:


    @staticmethod
    def get_strategy(

        pricing_type

    ):

        strategies = {

            'standard': StandardPricing(),

            'happy_hour': HappyHourPricing(),

            'weekend': WeekendPricing(),

            'vip': VIPPricing(),

        }

        return strategies.get(

            pricing_type,

            StandardPricing()

        )