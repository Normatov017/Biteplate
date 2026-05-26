from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Paragraph
from reportlab.platypus import Spacer

from reportlab.lib.styles import getSampleStyleSheet

from reportlab.lib.pagesizes import letter

from io import BytesIO


# =========================
# GENERATE PDF RECEIPT
# =========================

def generate_pdf_receipt(

    order_items,

    total,

    payment_method,

    cashier,

):

    buffer = BytesIO()

    doc = SimpleDocTemplate(

        buffer,

        pagesize=letter

    )

    styles = getSampleStyleSheet()

    elements = []


    # =========================
    # HEADER
    # =========================

    elements.append(

        Paragraph(

            'BITEPLATE POS',

            styles['Title']

        )

    )

    elements.append(
        Spacer(1, 12)
    )


    # =========================
    # ITEMS
    # =========================

    for item in order_items:

        elements.append(

            Paragraph(

                f'{item["product"].name} '
                f'x{item["quantity"]} '
                f'- '
                f'{item["subtotal"]} UZS',

                styles['BodyText']

            )

        )

        elements.append(
            Spacer(1, 6)
        )


    # =========================
    # TOTAL
    # =========================

    elements.append(
        Spacer(1, 12)
    )

    elements.append(

        Paragraph(

            f'TOTAL: {total} UZS',

            styles['Heading2']

        )

    )

    elements.append(

        Paragraph(

            f'PAYMENT: {payment_method}',

            styles['BodyText']

        )

    )

    elements.append(

        Paragraph(

            f'CASHIER: {cashier}',

            styles['BodyText']

        )

    )


    # =========================
    # BUILD PDF
    # =========================

    doc.build(elements)

    pdf = buffer.getvalue()

    buffer.close()

    return pdf