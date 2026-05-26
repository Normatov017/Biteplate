from escpos.printer import Dummy

import qrcode

from io import BytesIO


# =========================
# PRINT RECEIPT
# =========================

def print_receipt(

    order_items,

    total,

    payment_method,

    cashier,

):

    printer = Dummy()


    # =========================
    # HEADER
    # =========================

    printer.set(

        align='center',

        bold=True,

        width=2,

        height=2

    )

    printer.text(
        'BITEPLATE POS\n'
    )

    printer.text(
        'Restaurant System\n\n'
    )


    # =========================
    # ITEMS
    # =========================

    printer.set(

        align='left',

        bold=False

    )

    for item in order_items:

        printer.text(

            f'{item["product"].name} '

            f'x{item["quantity"]}\n'

        )

        printer.text(

            f'{item["subtotal"]} UZS\n'

        )


    # =========================
    # TOTAL
    # =========================

    printer.text('\n')

    printer.set(
        bold=True
    )

    printer.text(

        f'TOTAL: {total} UZS\n'

    )

    printer.text(

        f'PAYMENT: {payment_method}\n'

    )

    printer.text(

        f'CASHIER: {cashier}\n'

    )


    # =========================
    # QR CODE
    # =========================

    qr = qrcode.make(
        'https://biteplate.uz'
    )

    buffer = BytesIO()

    qr.save(buffer)

    buffer.seek(0)

    printer.image(buffer)


    # =========================
    # FOOTER
    # =========================

    printer.text('\n')

    printer.set(
        align='center'
    )

    printer.text(
        'Thank you!\n'
    )

    printer.cut()


    # =========================
    # OUTPUT
    # =========================

    print(

        printer.output

    )