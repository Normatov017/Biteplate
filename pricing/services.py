from decimal import Decimal


class PricingStrategy:

    def calculate_total(self, order):

        raise NotImplementedError

    def calculateTotal(self, order):

        return self.calculate_total(order)

    def bonus_items(self, order):

        return []


class StandardPricing(PricingStrategy):

    def calculate_total(self, order):

        total = 0

        for item in order.items.all():
            total += item.get_total()

        return total


class HappyHourPricing(PricingStrategy):

    def calculate_total(self, order):

        total = 0

        for item in order.items.all():
            total += item.get_total()

        discount = total * Decimal('0.20')

        return total - discount


class LoyaltyPricing(PricingStrategy):

    def calculate_total(self, order):

        total = 0

        for item in order.items.all():
            total += item.get_total()

        discount = total * Decimal('0.10')

        return total - discount

    def bonus_items(self, order):

        return ['Free drink']


class LoyaltyCardPricing(LoyaltyPricing):

    pass
