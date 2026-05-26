from decimal import Decimal
from decimal import InvalidOperation

from django import template


register = template.Library()


def _as_decimal(value):

    try:

        return Decimal(str(value or 0))

    except (InvalidOperation, TypeError, ValueError):

        return Decimal('0')


@register.filter
def money(value, currency='UZS'):

    amount = _as_decimal(value)
    currency = (currency or 'UZS').upper()

    if currency == 'UZS':

        rounded = int(amount.quantize(Decimal('1')))
        return f"{rounded:,}".replace(',', ' ') + " so'm"

    if currency == 'RUB':

        rounded = int(amount.quantize(Decimal('1')))
        return f"{rounded:,}".replace(',', ' ') + ' ₽'

    if currency == 'USD':

        return f"${amount:,.2f}"

    return f"{amount:,.2f} {currency}"
