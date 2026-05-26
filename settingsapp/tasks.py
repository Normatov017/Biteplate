from celery import shared_task
from django.utils import timezone

from settingsapp.models import SystemSettings
from settingsapp.telegram_reports import send_daily_report


@shared_task
def send_scheduled_telegram_report():

    now = timezone.localtime()
    sent = 0

    for settings in SystemSettings.objects.filter(
        telegram_reports_enabled=True
    ):

        if (
            not settings.telegram_report_time
            or settings.telegram_last_report_date == now.date()
            or settings.telegram_report_time.hour != now.hour
            or settings.telegram_report_time.minute != now.minute
        ):

            continue

        ok, _message = send_daily_report(now.date())

        if ok:

            settings.telegram_last_report_date = now.date()
            settings.save(
                update_fields=[
                    'telegram_last_report_date',
                    'updated_at'
                ]
            )
            sent += 1

    return sent
