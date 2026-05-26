from django.test import SimpleTestCase

from commandengine.commands import (
    CancelOrderCommand,
    PrepareOrderCommand,
    ReadyOrderCommand
)
from commandengine.services import KitchenQueue


class DummyOrder:

    def __init__(self):

        self.status = 'pending'
        self.kitchen_status = 'waiting'
        self.priority = 2
        self.created_at = 1
        self.saved = 0

    def save(self):

        self.saved += 1


class CommandPatternTests(SimpleTestCase):

    def test_prepare_command_execute_and_undo(self):

        order = DummyOrder()
        queue = KitchenQueue()

        queue.run(PrepareOrderCommand(order))

        self.assertEqual(order.status, 'preparing')
        self.assertEqual(order.kitchen_status, 'preparing')

        queue.undo_last()

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.kitchen_status, 'waiting')

    def test_ready_and_cancel_commands(self):

        order = DummyOrder()

        ReadyOrderCommand(order).execute()
        self.assertEqual(order.status, 'ready')

        CancelOrderCommand(order).execute()
        self.assertEqual(order.kitchen_status, 'cancelled')

    def test_reprioritize_orders(self):

        low = DummyOrder()
        high = DummyOrder()
        high.priority = 9

        ordered = KitchenQueue().reprioritize([low, high])

        self.assertEqual(ordered[0], high)
