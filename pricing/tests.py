from decimal import Decimal

from django.test import SimpleTestCase

from pricing.services import (
    HappyHourPricing,
    LoyaltyCardPricing,
    StandardPricing
)


class DummyItem:

    def __init__(self, total):

        self.total = Decimal(str(total))

    def get_total(self):

        return self.total


class DummyItems:

    def all(self):

        return [
            DummyItem('100000'),
            DummyItem('50000')
        ]


class DummyOrder:

    items = DummyItems()


class PricingStrategyTests(SimpleTestCase):

    def test_standard_pricing(self):

        self.assertEqual(
            StandardPricing().calculateTotal(DummyOrder()),
            Decimal('150000')
        )

    def test_happy_hour_pricing(self):

        self.assertEqual(
            HappyHourPricing().calculate_total(DummyOrder()),
            Decimal('120000.00')
        )

    def test_loyalty_card_pricing_and_bonus(self):

        strategy = LoyaltyCardPricing()

        self.assertEqual(
            strategy.calculate_total(DummyOrder()),
            Decimal('135000.00')
        )
        self.assertEqual(strategy.bonus_items(DummyOrder()), ['Free drink'])
