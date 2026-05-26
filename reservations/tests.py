from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from orders.models import Table
from reservations.models import Reservation
from reservations.services import due_reservations
from reservations.services import reservation_staff_message
from reservations.services import send_due_reservation_reminders


class ReservationReminderTests(TestCase):

    def setUp(self):

        self.table = Table.objects.create(
            table_number=3,
            seats=4,
            status='reserved'
        )

    def _reservation(self, **overrides):

        values = {
            'customer_name': 'Test Guest',
            'phone_number': '+998901234567',
            'table': self.table,
            'reservation_time': timezone.now() + timedelta(minutes=20),
            'end_time': timezone.now() + timedelta(hours=2),
            'guest_count': 4,
            'status': 'confirmed',
        }
        values.update(overrides)
        return Reservation.objects.create(**values)

    def test_due_reservations_include_upcoming_confirmed_only(self):

        due = self._reservation()
        self._reservation(
            reservation_time=timezone.now() + timedelta(hours=2)
        )
        self._reservation(
            status='cancelled'
        )

        self.assertEqual(
            list(due_reservations()),
            [due]
        )

    def test_reminder_is_sent_once(self):

        reservation = self._reservation()

        with patch(
            'reservations.services.send_telegram_text',
            return_value=(True, 'ok')
        ) as sender:

            first = send_due_reservation_reminders()
            second = send_due_reservation_reminders()

        reservation.refresh_from_db()
        self.assertEqual(first['sent'], 1)
        self.assertEqual(second['sent'], 0)
        self.assertIsNotNone(reservation.reminder_sent_at)
        self.assertEqual(sender.call_count, 1)

    def test_message_contains_staff_context(self):

        reservation = self._reservation()
        message = reservation_staff_message(reservation)

        self.assertIn('Table:</b> 3', message)
        self.assertIn('Test Guest', message)
        self.assertIn('4', message)
