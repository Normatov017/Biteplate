from django.test import SimpleTestCase

from historylog.services import OrderHistoryLogger


class OrderHistoryLoggerTests(SimpleTestCase):

    def test_singleton_instance(self):

        self.assertIs(
            OrderHistoryLogger(),
            OrderHistoryLogger()
        )
