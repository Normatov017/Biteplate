import json
import socket
import ssl
from datetime import timedelta
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.utils import timezone
from django.db.models import Q

from settingsapp.models import SystemSettings
from settingsapp.telegram_reports import _telegram_ssl_context

from .models import Reservation


def _local_range(reservation):

    start = timezone.localtime(
        reservation.reservation_time
    )
    end = reservation.end_time

    if end:

        end = timezone.localtime(end)

    if not end:

        return start.strftime('%d.%m.%Y %H:%M')

    return (
        f"{start:%d.%m.%Y %H:%M} - "
        f"{end:%H:%M}"
    )


def reservation_staff_message(reservation, title='RESERVATION REMINDER'):

    phone = reservation.phone_number or '-'
    return '\n'.join([
        f'<b>{title}</b>',
        f'<b>Table:</b> {reservation.table.table_number}',
        f'<b>Guest:</b> {reservation.customer_name}',
        f'<b>Guests:</b> {reservation.guest_count}',
        f'<b>Time:</b> {_local_range(reservation)}',
        f'<b>Phone:</b> {phone}',
        '',
        (
            'Guest kelmasa, belgilangan vaqtdan 30 minut keyin '
            'bron avtomatik bekor qilinadi.'
        ),
    ])


def send_telegram_text(text, timeout=8):

    settings = SystemSettings.objects.first()

    if (
        not settings
        or not settings.telegram_bot_token
        or not settings.telegram_chat_id
    ):

        return False, 'Telegram bot token yoki chat ID kiritilmagan.'

    payload = urlencode({
        'chat_id': settings.telegram_chat_id,
        'text': text,
        'parse_mode': 'HTML',
    }).encode()
    url = f'https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage'

    try:

        with urlopen(
            url,
            data=payload,
            timeout=timeout,
            context=_telegram_ssl_context()
        ) as response:

            data = json.loads(response.read().decode('utf-8'))

    except HTTPError as exc:

        return False, f'Telegram HTTP xato: {exc.code}. Bot token yoki chat ID ni tekshiring.'

    except ssl.SSLCertVerificationError:

        return False, (
            'Telegram SSL sertifikat xatosi. Python CA chain Telegramni '
            'tekshirolmayapti.'
        )

    except (socket.timeout, TimeoutError, URLError, OSError):

        return False, (
            'Telegramga ulanish timeout bo‘ldi. Server internet/proxy orqali '
            'api.telegram.org ga chiqa olmayapti.'
        )

    return bool(data.get('ok')), data.get('description') or 'Reminder sent.'


def send_reservation_confirmation(reservation):

    if reservation.confirmation_sent_at:

        return True, 'Confirmation already sent.'

    ok, message = send_telegram_text(
        reservation_staff_message(
            reservation,
            title='NEW RESERVATION'
        )
    )

    if ok:

        reservation.confirmation_sent_at = timezone.now()
        reservation.last_reminder_error = ''
        reservation.save(
            update_fields=[
                'confirmation_sent_at',
                'last_reminder_error',
            ]
        )

    else:

        reservation.last_reminder_error = message
        reservation.save(
            update_fields=[
                'last_reminder_error',
            ]
        )

    return ok, message


def due_reservations(now=None, window_minutes=30):

    now = now or timezone.now()
    reminder_until = now + timedelta(
        minutes=window_minutes
    )
    still_relevant_from = now - timedelta(
        minutes=30
    )

    retry_before = now - timedelta(
        minutes=5
    )

    return Reservation.objects.select_related(
        'table'
    ).filter(
        status='confirmed',
        reminder_sent_at__isnull=True,
        reservation_time__gte=still_relevant_from,
        reservation_time__lte=reminder_until
    ).filter(
        Q(last_reminder_attempt_at__isnull=True)
        | Q(last_reminder_attempt_at__lte=retry_before)
    ).order_by(
        'reservation_time'
    )


def send_due_reservation_reminders(now=None, window_minutes=30):

    sent = 0
    failed = 0
    skipped = 0
    errors = []

    for reservation in due_reservations(
        now=now,
        window_minutes=window_minutes
    ):

        reservation.last_reminder_attempt_at = timezone.now()
        reservation.save(
            update_fields=[
                'last_reminder_attempt_at',
            ]
        )

        ok, message = send_telegram_text(
            reservation_staff_message(reservation)
        )

        if ok:

            reservation.reminder_sent_at = timezone.now()
            reservation.last_reminder_error = ''
            reservation.save(
                update_fields=[
                    'reminder_sent_at',
                    'last_reminder_attempt_at',
                    'last_reminder_error',
                ]
            )
            sent += 1
            continue

        reservation.last_reminder_error = message
        reservation.save(
            update_fields=[
                'last_reminder_error',
            ]
        )
        failed += 1
        errors.append(
            f'Table {reservation.table.table_number}: {message}'
        )

    return {
        'sent': sent,
        'failed': failed,
        'skipped': skipped,
        'errors': errors,
    }
