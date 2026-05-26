from django.db import models

from restaurants.models import Restaurant
from restaurants.models import Branch


# =========================
# SYSTEM SETTINGS
# =========================

class SystemSettings(models.Model):

    restaurant = models.ForeignKey(

        Restaurant,

        on_delete=models.CASCADE,

        related_name='settings'

    )

    branch = models.ForeignKey(

        Branch,

        on_delete=models.CASCADE,

        related_name='settings',

        null=True,

        blank=True

    )

    # =========================
    # GENERAL
    # =========================

    currency = models.CharField(

        max_length=10,

        default='UZS'

    )

    usd_to_base_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=12020
    )

    rub_to_base_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=135
    )

    timezone = models.CharField(

        max_length=100,

        default='Asia/Tashkent'

    )

    language = models.CharField(

        max_length=20,

        default='uz'

    )

    tax_percent = models.DecimalField(

        max_digits=5,

        decimal_places=2,

        default=12

    )

    service_fee_percent = models.DecimalField(

        max_digits=5,

        decimal_places=2,

        default=0

    )

    waiter_commission_percent = models.DecimalField(

        max_digits=5,

        decimal_places=2,

        default=1

    )

    waiter_daily_fixed_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=50000
    )

    # =========================
    # POS SETTINGS
    # =========================

    auto_print_receipt = models.BooleanField(
        default=False
    )

    enable_split_bill = models.BooleanField(
        default=True
    )

    enable_qr_menu = models.BooleanField(
        default=True
    )

    # =========================
    # KITCHEN SETTINGS
    # =========================

    auto_send_kitchen = models.BooleanField(
        default=True
    )

    kitchen_sound_alerts = models.BooleanField(
        default=True
    )

    # =========================
    # INVENTORY SETTINGS
    # =========================

    low_stock_alert = models.BooleanField(
        default=True
    )

    auto_inventory_deduction = models.BooleanField(
        default=True
    )

    # =========================
    # HR SETTINGS
    # =========================

    shift_management = models.BooleanField(
        default=True
    )

    attendance_tracking = models.BooleanField(
        default=True
    )

    # =========================
    # ACCOUNTING SETTINGS
    # =========================

    enable_accounting = models.BooleanField(
        default=True
    )

    fiscal_year_start = models.DateField(
        null=True,
        blank=True
    )

    # =========================
    # RECEIPT SETTINGS
    # =========================

    receipt_footer = models.TextField(
        blank=True,
        null=True
    )

    receipt_header = models.CharField(
        max_length=255,
        default='Premium Restaurant OS'
    )

    receipt_show_waiter = models.BooleanField(
        default=True
    )

    # =========================
    # TELEGRAM REPORTS
    # =========================

    telegram_reports_enabled = models.BooleanField(
        default=False
    )

    telegram_bot_token = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    telegram_chat_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    telegram_report_time = models.TimeField(
        null=True,
        blank=True
    )

    telegram_last_report_date = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return (

            f'Settings - '

            f'{self.restaurant.name}'

        )
