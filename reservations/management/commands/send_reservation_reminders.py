from django.core.management.base import BaseCommand

from reservations.services import send_due_reservation_reminders


class Command(BaseCommand):

    help = 'Send Telegram reminders for reservations due soon.'

    def add_arguments(self, parser):

        parser.add_argument(
            '--window',
            type=int,
            default=30,
            help='Reminder window in minutes.'
        )

    def handle(self, *args, **options):

        result = send_due_reservation_reminders(
            window_minutes=options['window']
        )
        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"sent={result['sent']} "
                    f"failed={result['failed']} "
                    f"skipped={result['skipped']}"
                )
            )
        )

        for error in result['errors']:

            self.stdout.write(
                self.style.WARNING(error)
            )
