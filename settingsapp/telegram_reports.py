import json
import socket
import ssl
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.db.models import Q, Sum
from django.utils import timezone
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table as RLTable,
    TableStyle,
)

from accounts.models import User
from billing.models import Payment
from inventory.models import InventoryWaste, Product, Purchase
from orders.models import Order, OrderItem, Table as DiningTable
from settingsapp.models import SystemSettings
from shifts.models import CashMovement, Shift, ShiftLog


ACCENT = colors.HexColor('#f8b900')
INK = colors.HexColor('#0f172a')
MUTED = colors.HexColor('#64748b')
PANEL = colors.HexColor('#f8fafc')
LINE = colors.HexColor('#e2e8f0')
GREEN = colors.HexColor('#22c55e')
BLUE = colors.HexColor('#38bdf8')
PURPLE = colors.HexColor('#7c3aed')


def _telegram_ssl_context():

    system_cert = Path('/etc/ssl/cert.pem')

    if system_cert.exists():

        return ssl.create_default_context(
            cafile=str(system_cert)
        )

    return ssl.create_default_context()


def _decimal(value):

    return Decimal(str(value or 0))


def _sum_decimal(values):

    total = Decimal('0')

    for value in values:

        total += _decimal(value)

    return total


def _money(value, currency='UZS'):

    amount = _decimal(value)
    code = (currency or 'UZS').upper()

    if code == 'UZS':

        return f"{amount:,.0f}".replace(',', ' ') + " so'm"

    if code == 'RUB':

        return f"{amount:,.2f}".replace(',', ' ') + ' RUB'

    if code == 'USD':

        return '$' + f'{amount:,.2f}'

    return f"{amount:,.2f} {code}".replace(',', ' ')


def _name(user):

    if not user:

        return 'No waiter'

    return user.full_name or user.username


def _safe_total(order):

    try:

        return _decimal(order.calculate_total())

    except Exception:

        return _decimal(order.total_amount)


def _date_range(day):

    start = timezone.make_aware(
        datetime.combine(day, datetime.min.time())
    )
    end = start + timedelta(days=1)
    return start, end


def _paid_orders_for(payments):

    order_ids = list(
        payments.exclude(order_id=None)
        .values_list('order_id', flat=True)
        .distinct()
    )

    return Order.objects.filter(id__in=order_ids).select_related(
        'waiter',
        'table',
    )


def build_daily_report_data(day=None):

    day = day or timezone.localdate()
    settings = SystemSettings.objects.first()
    currency = (settings.currency if settings else 'UZS') or 'UZS'
    start, end = _date_range(day)

    payments = Payment.objects.filter(
        status='paid',
        created_at__gte=start,
        created_at__lt=end,
    ).select_related(
        'order',
        'order__waiter',
        'order__table',
    )
    refunds = Payment.objects.filter(
        status='refunded',
        created_at__gte=start,
        created_at__lt=end,
    )
    orders = Order.objects.filter(
        created_at__gte=start,
        created_at__lt=end,
    ).select_related(
        'waiter',
        'table',
    )
    paid_orders = _paid_orders_for(payments)
    purchases = Purchase.objects.filter(
        created_at__gte=start,
        created_at__lt=end,
    ).select_related('supplier')
    movements = CashMovement.objects.filter(
        created_at__gte=start,
        created_at__lt=end,
    ).select_related('created_by')

    revenue = _sum_decimal(payments.values_list('amount', flat=True))
    refund_total = _sum_decimal(refunds.values_list('refunded_amount', flat=True))
    purchase_total = _sum_decimal(purchases.values_list('total_amount', flat=True))
    cash_in = _sum_decimal(
        movements.filter(movement_type='in').values_list('amount', flat=True)
    )
    cash_out = _sum_decimal(
        movements.filter(movement_type='out').values_list('amount', flat=True)
    )
    net_revenue = revenue - refund_total
    net_profit = net_revenue + cash_in - purchase_total - cash_out
    order_count = paid_orders.count()
    active_order_count = Order.objects.exclude(
        status__in=['completed', 'cancelled']
    ).count()
    average_check = net_revenue / order_count if order_count else Decimal('0')

    method_totals = dict(
        payments.values('method').annotate(total=Sum('amount')).values_list(
            'method',
            'total',
        )
    )
    payment_rows = []

    for method, label in Payment.METHOD_CHOICES:

        total = _decimal(method_totals.get(method))
        payment_rows.append({
            'method': method,
            'label': label,
            'total': total,
        })

    item_rows = (
        OrderItem.objects.filter(
            order__in=paid_orders,
            refunded=False,
        )
        .values('menu_item__name')
        .annotate(quantity=Sum('quantity'))
        .order_by('-quantity')[:8]
    )
    top_products = [
        {
            'name': row['menu_item__name'] or 'Product',
            'quantity': row['quantity'] or 0,
        }
        for row in item_rows
    ]

    waiters = User.objects.filter(
        Q(role__name__icontains='waiter')
        | Q(role__name__icontains='server')
        | Q(role__name__icontains='offitsiant')
        | Q(role__name__icontains='ofitsiant')
    ).filter(status='active').select_related('role')

    if not waiters.exists():

        waiters = User.objects.filter(
            served_orders__isnull=False
        ).distinct().select_related('role')

    commission_percent = (
        _decimal(settings.waiter_commission_percent)
        if settings else Decimal('1')
    )
    fixed_pay = (
        _decimal(settings.waiter_daily_fixed_pay)
        if settings else Decimal('0')
    )
    waiter_rows = []

    for waiter in waiters:

        waiter_paid_orders = paid_orders.filter(waiter=waiter)
        waiter_order_ids = list(waiter_paid_orders.values_list('id', flat=True))
        waiter_sales = _sum_decimal(
            payments.filter(order_id__in=waiter_order_ids)
            .values_list('amount', flat=True)
        )
        commission = waiter_sales * commission_percent / Decimal('100')
        daily_fixed = fixed_pay if waiter_paid_orders.exists() else Decimal('0')
        current_log = ShiftLog.objects.filter(
            employee=waiter,
            clock_in__date=day,
            clock_out__isnull=True,
        ).first()

        waiter_rows.append({
            'name': _name(waiter),
            'orders': waiter_paid_orders.count(),
            'sales': waiter_sales,
            'fixed': daily_fixed,
            'commission': commission,
            'total': daily_fixed + commission,
            'status': 'Online' if waiter.is_online or current_log else 'Offline',
        })

    waiter_rows.sort(key=lambda row: row['total'], reverse=True)

    kitchen_rows = []

    for status, label in Order.KITCHEN_STATUS:

        if status == 'cancelled':

            continue

        kitchen_rows.append({
            'label': label,
            'count': Order.objects.filter(kitchen_status=status).count(),
        })

    table_rows = []

    for status, label in DiningTable.STATUS_CHOICES:

        table_rows.append({
            'label': label,
            'count': DiningTable.objects.filter(status=status).count(),
        })

    low_stock = [
        {
            'name': product.name,
            'quantity': product.quantity,
            'unit': product.get_unit_display(),
        }
        for product in Product.objects.order_by('quantity')[:8]
        if product.is_low_stock()
    ]

    last_purchases = [
        {
            'invoice': purchase.invoice_number,
            'supplier': purchase.supplier.name,
            'status': purchase.get_status_display(),
            'due': purchase.due_date,
            'total': _decimal(purchase.total_amount),
        }
        for purchase in purchases.order_by('-created_at')[:8]
    ]

    cash_rows = [
        {
            'type': movement.get_movement_type_display(),
            'amount': movement.signed_amount(),
            'reason': movement.reason,
        }
        for movement in movements.order_by('-created_at')[:8]
    ]

    sales_7_days = []

    for offset in range(6, -1, -1):

        current_day = day - timedelta(days=offset)
        day_total = Payment.objects.filter(
            status='paid',
            created_at__date=current_day,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        sales_7_days.append({
            'label': current_day.strftime('%d.%m'),
            'total': _decimal(day_total),
        })

    hourly_sales = []

    for hour in range(8, 24):

        hour_total = Decimal('0')

        for payment in payments:

            local_time = timezone.localtime(payment.created_at)

            if local_time.hour == hour:

                hour_total += _decimal(payment.amount)

        hourly_sales.append({
            'label': f'{hour:02d}:00',
            'total': hour_total,
        })

    open_shifts = Shift.objects.filter(status='open').count()
    closed_shifts = Shift.objects.filter(
        status='closed',
        closed_at__date=day,
    ).count()
    waste_count = InventoryWaste.objects.filter(created_at__date=day).count()

    return {
        'day': day,
        'generated_at': timezone.localtime(),
        'settings': settings,
        'currency': currency,
        'revenue': revenue,
        'refund_total': refund_total,
        'net_revenue': net_revenue,
        'purchase_total': purchase_total,
        'cash_in': cash_in,
        'cash_out': cash_out,
        'net_profit': net_profit,
        'order_count': order_count,
        'active_order_count': active_order_count,
        'average_check': average_check,
        'payment_rows': payment_rows,
        'top_products': top_products,
        'waiter_rows': waiter_rows,
        'kitchen_rows': kitchen_rows,
        'table_rows': table_rows,
        'low_stock': low_stock,
        'purchases': last_purchases,
        'cash_rows': cash_rows,
        'sales_7_days': sales_7_days,
        'hourly_sales': hourly_sales,
        'open_shifts': open_shifts,
        'closed_shifts': closed_shifts,
        'waste_count': waste_count,
        'cash_delta': cash_in - cash_out,
    }


def build_daily_report(day=None):

    data = build_daily_report_data(day)
    currency = data['currency']

    payment_lines = [
        f"- {row['label']}: {_money(row['total'], currency)}"
        for row in data['payment_rows']
        if row['total']
    ]
    waiter_lines = [
        (
            f"- {row['name']}: {row['orders']} order, "
            f"sales {_money(row['sales'], currency)}, "
            f"KPI {_money(row['total'], currency)}"
        )
        for row in data['waiter_rows'][:5]
    ]
    product_lines = [
        f"- {row['name']}: x{row['quantity']}"
        for row in data['top_products'][:5]
    ]
    stock_lines = [
        f"- {row['name']}: {row['quantity']} {row['unit']}"
        for row in data['low_stock'][:5]
    ]

    return '\n'.join([
        f"BitePlate management report - {data['day']:%d.%m.%Y}",
        f"Net revenue: {_money(data['net_revenue'], currency)}",
        f"Orders: {data['order_count']} paid, {data['active_order_count']} active",
        f"Average check: {_money(data['average_check'], currency)}",
        f"Expenses: {_money(data['purchase_total'], currency)}",
        f"Cash delta: {_money(data['cash_delta'], currency)}",
        f"Net profit: {_money(data['net_profit'], currency)}",
        '',
        'Payment mix:',
        '\n'.join(payment_lines) or '- No payments',
        '',
        'Waiter KPI:',
        '\n'.join(waiter_lines) or '- No waiter sales',
        '',
        'Top products:',
        '\n'.join(product_lines) or '- No products sold',
        '',
        'Inventory alerts:',
        '\n'.join(stock_lines) or '- Stock is healthy',
    ])


def build_daily_report_pdf(day=None):

    data = build_daily_report_data(day)
    currency = data['currency']
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=12 * mm,
        title='BitePlate Management Report',
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=INK,
        alignment=TA_CENTER,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='Muted',
        parent=styles['Normal'],
        fontSize=8,
        textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name='Section',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=INK,
        spaceBefore=8,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name='Right',
        parent=styles['Normal'],
        alignment=TA_RIGHT,
    ))

    story = []
    header = [
        [
            Paragraph('BitePlate Management Report', styles['ReportTitle']),
        ],
        [
            Paragraph(
                (
                    f"{data['day']:%d.%m.%Y}  |  "
                    f"Generated {data['generated_at']:%H:%M}  |  "
                    f"Currency {currency}"
                ),
                styles['Muted'],
            )
        ],
    ]
    story.append(RLTable(header, colWidths=[250 * mm]))
    story.append(Spacer(1, 8))

    kpi_data = [
        ['Net revenue', 'Orders', 'Average check', 'Expenses', 'Net profit', 'Cash delta'],
        [
            _money(data['net_revenue'], currency),
            str(data['order_count']),
            _money(data['average_check'], currency),
            _money(data['purchase_total'], currency),
            _money(data['net_profit'], currency),
            _money(data['cash_delta'], currency),
        ],
    ]
    kpi = RLTable(kpi_data, colWidths=[39 * mm] * 6, rowHeights=[12 * mm, 15 * mm])
    kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PANEL),
        ('TEXTCOLOR', (0, 0), (-1, 0), MUTED),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 15),
        ('BOX', (0, 0), (-1, -1), 0.6, LINE),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi)
    story.append(Spacer(1, 10))

    story.append(_charts_row(data, currency))
    story.append(Spacer(1, 8))

    story.append(_two_column_tables(data, currency, styles))
    story.append(Spacer(1, 8))

    story.append(Paragraph('Employee earnings', styles['Section']))
    story.append(_waiter_table(data, currency))

    story.append(PageBreak())
    story.append(Paragraph('Operations detail', styles['Section']))
    story.append(_operations_tables(data, currency, styles))

    doc.build(story, onFirstPage=_pdf_footer, onLaterPages=_pdf_footer)
    buffer.seek(0)
    return buffer.read()


def _pdf_footer(canvas_obj, doc):

    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 7)
    canvas_obj.setFillColor(MUTED)
    canvas_obj.drawString(16 * mm, 8 * mm, 'BitePlate Restaurant OS')
    canvas_obj.drawRightString(
        doc.pagesize[0] - 16 * mm,
        8 * mm,
        f'Page {doc.page}',
    )
    canvas_obj.restoreState()


def _bar_chart(title, rows, color=GREEN):

    drawing = Drawing(360, 150)
    chart = VerticalBarChart()
    chart.x = 30
    chart.y = 25
    chart.width = 300
    chart.height = 90
    values = [float(row['total'] or 0) for row in rows]
    chart.data = [values or [0]]
    chart.categoryAxis.categoryNames = [row['label'] for row in rows] or ['']
    chart.valueAxis.valueMin = 0
    chart.bars[0].fillColor = color
    chart.barSpacing = 2
    chart.groupSpacing = 10
    chart.categoryAxis.labels.fontSize = 6
    chart.valueAxis.labels.fontSize = 6
    drawing.add(chart)
    drawing.add(String(18, 130, title, fontName='Helvetica-Bold', fontSize=10))
    return drawing


def _pie_chart(title, rows):

    drawing = Drawing(220, 150)
    pie = Pie()
    pie.x = 65
    pie.y = 30
    pie.width = 85
    pie.height = 85
    active = [row for row in rows if row['total']]
    pie.data = [float(row['total']) for row in active] or [1]
    pie.labels = [row['label'] for row in active] or ['No sales']
    palette = [GREEN, ACCENT, BLUE, PURPLE, colors.HexColor('#f97316'), colors.HexColor('#94a3b8')]

    for index, color in enumerate(palette):

        if index < len(pie.slices):

            pie.slices[index].fillColor = color

    drawing.add(pie)
    drawing.add(String(14, 130, title, fontName='Helvetica-Bold', fontSize=10))
    return drawing


def _charts_row(data, currency):

    chart_table = RLTable(
        [[
            _bar_chart('7 kunlik savdo', data['sales_7_days'], GREEN),
            _pie_chart('Payment mix', data['payment_rows']),
            _bar_chart('Bugungi soatlar', data['hourly_sales'], ACCENT),
        ]],
        colWidths=[92 * mm, 62 * mm, 92 * mm],
    )
    chart_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, LINE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    return chart_table


def _mini_table(title, headings, rows, col_widths):

    table_data = [[title] + [''] * (len(headings) - 1), headings] + rows
    table = RLTable(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), INK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, 1), PANEL),
        ('TEXTCOLOR', (0, 1), (-1, 1), MUTED),
        ('BOX', (0, 0), (-1, -1), 0.5, LINE),
        ('INNERGRID', (0, 1), (-1, -1), 0.35, LINE),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return table


def _two_column_tables(data, currency, styles):

    payment_rows = [
        [row['label'], _money(row['total'], currency)]
        for row in data['payment_rows']
    ] or [['No payments', '-']]
    top_rows = [
        [row['name'], f"x{row['quantity']}"]
        for row in data['top_products']
    ] or [['No products', '-']]
    kitchen_rows = [
        [row['label'], str(row['count'])]
        for row in data['kitchen_rows']
    ]
    floor_rows = [
        [row['label'], str(row['count'])]
        for row in data['table_rows']
    ]

    left = _mini_table(
        'Payment totals',
        ['Method', 'Total'],
        payment_rows,
        [42 * mm, 42 * mm],
    )
    middle = _mini_table(
        'Top products',
        ['Product', 'Qty'],
        top_rows[:8],
        [55 * mm, 22 * mm],
    )
    right = _mini_table(
        'Kitchen / Floor',
        ['Status', 'Count'],
        kitchen_rows + [['', '']] + floor_rows,
        [42 * mm, 25 * mm],
    )
    table = RLTable([[left, middle, right]], colWidths=[88 * mm, 82 * mm, 72 * mm])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return table


def _waiter_table(data, currency):

    rows = [
        ['Employee', 'Orders', 'Sales', 'Fixed', 'Bonus', 'Total KPI', 'Status']
    ]

    for row in data['waiter_rows'][:12]:

        rows.append([
            row['name'],
            str(row['orders']),
            _money(row['sales'], currency),
            _money(row['fixed'], currency),
            _money(row['commission'], currency),
            _money(row['total'], currency),
            row['status'],
        ])

    if len(rows) == 1:

        rows.append(['No waiter data', '-', '-', '-', '-', '-', '-'])

    table = RLTable(
        rows,
        colWidths=[47 * mm, 18 * mm, 33 * mm, 33 * mm, 33 * mm, 34 * mm, 24 * mm],
    )
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), INK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, LINE),
        ('INNERGRID', (0, 0), (-1, -1), 0.35, LINE),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def _operations_tables(data, currency, styles):

    stock_rows = [
        [row['name'], f"{row['quantity']} {row['unit']}"]
        for row in data['low_stock']
    ] or [['Stock is healthy', '-']]
    purchase_rows = [
        [
            row['invoice'],
            row['supplier'],
            row['status'],
            row['due'].strftime('%d.%m.%Y') if row['due'] else '-',
            _money(row['total'], currency),
        ]
        for row in data['purchases']
    ] or [['No purchases', '-', '-', '-', '-']]
    cash_rows = [
        [row['type'], _money(row['amount'], currency), row['reason']]
        for row in data['cash_rows']
    ] or [['No cash movements', '-', '-']]
    shift_rows = [
        ['Open shifts', str(data['open_shifts'])],
        ['Closed shifts today', str(data['closed_shifts'])],
        ['Waste records', str(data['waste_count'])],
    ]

    stock = _mini_table(
        'Inventory alerts',
        ['Product', 'Qty'],
        stock_rows,
        [60 * mm, 32 * mm],
    )
    shifts = _mini_table(
        'Waste & shifts',
        ['Metric', 'Value'],
        shift_rows,
        [55 * mm, 28 * mm],
    )
    purchase = _mini_table(
        'Purchases',
        ['Invoice', 'Supplier', 'Status', 'Due', 'Total'],
        purchase_rows,
        [38 * mm, 48 * mm, 28 * mm, 28 * mm, 36 * mm],
    )
    cash = _mini_table(
        'Cash movements',
        ['Type', 'Amount', 'Reason'],
        cash_rows,
        [35 * mm, 42 * mm, 90 * mm],
    )

    table = RLTable(
        [
            [stock, shifts],
            [purchase, ''],
            [cash, ''],
        ],
        colWidths=[180 * mm, 90 * mm],
    )
    table.setStyle(TableStyle([
        ('SPAN', (0, 1), (-1, 1)),
        ('SPAN', (0, 2), (-1, 2)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return table


def _multipart_payload(fields, files):

    boundary = f'----BitePlate{uuid.uuid4().hex}'
    body = BytesIO()

    for name, value in fields.items():

        body.write(f'--{boundary}\r\n'.encode())
        body.write(
            (
                f'Content-Disposition: form-data; name="{name}"'
                f'\r\n\r\n{value}\r\n'
            ).encode()
        )

    for name, file_data in files.items():

        filename, content_type, content = file_data
        body.write(f'--{boundary}\r\n'.encode())
        body.write(
            (
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{filename}"\r\n'
                f'Content-Type: {content_type}\r\n\r\n'
            ).encode()
        )
        body.write(content)
        body.write(b'\r\n')

    body.write(f'--{boundary}--\r\n'.encode())
    return (
        body.getvalue(),
        f'multipart/form-data; boundary={boundary}'
    )


def send_daily_report(day=None):

    settings = SystemSettings.objects.first()

    if (
        not settings
        or not settings.telegram_bot_token
        or not settings.telegram_chat_id
    ):

        return False, 'Telegram bot token yoki chat ID kiritilmagan.'

    day = day or timezone.localdate()
    data = build_daily_report_data(day)
    currency = data['currency']
    pdf_bytes = build_daily_report_pdf(day)
    caption = '\n'.join([
        f"BitePlate management report - {day:%d.%m.%Y}",
        f"Net revenue: {_money(data['net_revenue'], currency)}",
        f"Orders: {data['order_count']} paid / {data['active_order_count']} active",
        f"Net profit: {_money(data['net_profit'], currency)}",
    ])
    payload, content_type = _multipart_payload(
        {
            'chat_id': settings.telegram_chat_id,
            'caption': caption,
        },
        {
            'document': (
                f'biteplate-daily-report-{day:%Y-%m-%d}.pdf',
                'application/pdf',
                pdf_bytes
            )
        }
    )
    url = f'https://api.telegram.org/bot{settings.telegram_bot_token}/sendDocument'

    try:

        request = Request(
            url,
            data=payload,
            headers={
                'Content-Type': content_type,
            }
        )

        with urlopen(
            request,
            timeout=12,
            context=_telegram_ssl_context()
        ) as response:

            data = json.loads(response.read().decode('utf-8'))

    except HTTPError as exc:

        return False, f'Telegram HTTP xato: {exc.code}. Bot token yoki chat ID ni tekshiring.'

    except ssl.SSLCertVerificationError:

        return False, (
            'Telegram SSL sertifikat xatosi. Python CA chain Telegramni '
            'tekshirolmayapti. macOS /etc/ssl/cert.pem ham ishlamadi.'
        )

    except (socket.timeout, TimeoutError, URLError, OSError):

        text_ok, text_message = send_daily_report_message(
            day=day,
            timeout=6
        )

        if text_ok:

            return True, (
                'PDF yuborilmadi, lekin matn report Telegramga yuborildi. '
                'Serverdan katta fayl yuborish/proxy sozlamasini tekshiring.'
            )

        return False, (
            'Telegramga ulanish timeout bo‘ldi. Server internet/proxy orqali '
            f'api.telegram.org ga chiqa olmayapti. Text fallback: {text_message}'
        )

    return bool(data.get('ok')), data.get('description') or 'PDF report sent.'


def send_daily_report_message(day=None, timeout=8):

    settings = SystemSettings.objects.first()

    if (
        not settings
        or not settings.telegram_bot_token
        or not settings.telegram_chat_id
    ):

        return False, 'Telegram bot token yoki chat ID kiritilmagan.'

    payload = urlencode({
        'chat_id': settings.telegram_chat_id,
        'text': build_daily_report(day),
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
            'tekshirolmayapti. macOS /etc/ssl/cert.pem ham ishlamadi.'
        )

    except (socket.timeout, TimeoutError, URLError, OSError):

        return False, (
            'Telegramga ulanish timeout bo‘ldi. Server internet/proxy orqali '
            'api.telegram.org ga chiqa olmayapti.'
        )

    return bool(data.get('ok')), data.get('description') or 'Report sent.'
