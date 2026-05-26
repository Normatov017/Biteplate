from django.core.management.base import BaseCommand

from settingsapp.telegram_reports import send_daily_report


class Command(BaseCommand):

    help = 'Send BitePlate daily dashboard to Telegram.'

    def handle(self, *args, **options):

        ok, message = send_daily_report()

        if ok:

            self.stdout.write(self.style.SUCCESS(message))

        else:

            self.stderr.write(message)
