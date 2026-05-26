from decimal import Decimal
from io import BytesIO
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.utils.text import slugify

from accounts.models import User
from billing.models import Payment
from inventory.models import Product
from inventory.models import Purchase
from inventory.models import PurchaseItem
from inventory.models import Supplier
from orders.models import Order
from orders.models import Table
from menu.models import ComboMeal
from menu.models import MenuItem
from permissionsapp.models import Role
from permissionsapp.utils import permission_required
from restaurants.models import Branch
from restaurants.models import Restaurant
from settingsapp.models import SystemSettings
from settingsapp.telegram_reports import send_daily_report
from shifts.models import CashMovement


def _xlsx_escape(value):

    return (
        str(value)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )


def _build_simple_xlsx(rows):

    sheet_rows = []

    for row_index, row in enumerate(rows, start=1):

        cells = []

        for column_index, value in enumerate(row, start=1):

            column = chr(64 + column_index)
            cells.append(
                (
                    f'<c r="{column}{row_index}" t="inlineStr">'
                    f'<is><t>{_xlsx_escape(value)}</t></is>'
                    f'</c>'
                )
            )

        sheet_rows.append(
            f'<row r="{row_index}">{"".join(cells)}</row>'
        )

    worksheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        '</worksheet>'
    )

    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Sales" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )

    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )

    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '</Types>'
    )

    output = BytesIO()

    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:

        archive.writestr('[Content_Types].xml', content_types)
        archive.writestr('_rels/.rels', rels)
        archive.writestr('xl/workbook.xml', workbook)
        archive.writestr('xl/_rels/workbook.xml.rels', workbook_rels)
        archive.writestr('xl/worksheets/sheet1.xml', worksheet)

    return output.getvalue()


@permission_required(
    'settings',
    'view'
)
def settings_dashboard(request):

    system_settings = SystemSettings.objects.first()

    if request.method == 'POST' and system_settings:

        system_settings.waiter_commission_percent = Decimal(
            request.POST.get(
                'waiter_commission_percent'
            ) or system_settings.waiter_commission_percent
        )
        system_settings.waiter_daily_fixed_pay = Decimal(
            request.POST.get(
                'waiter_daily_fixed_pay'
            ) or system_settings.waiter_daily_fixed_pay
        )
        system_settings.currency = request.POST.get(
            'currency',
            system_settings.currency
        )
        system_settings.usd_to_base_rate = Decimal(
            request.POST.get(
                'usd_to_base_rate'
            ) or system_settings.usd_to_base_rate
        )
        system_settings.rub_to_base_rate = Decimal(
            request.POST.get(
                'rub_to_base_rate'
            ) or system_settings.rub_to_base_rate
        )
        system_settings.receipt_header = request.POST.get(
            'receipt_header',
            system_settings.receipt_header
        )
        system_settings.receipt_footer = request.POST.get(
            'receipt_footer',
            system_settings.receipt_footer or ''
        )
        system_settings.receipt_show_waiter = (
            request.POST.get('receipt_show_waiter') == 'on'
        )
        system_settings.telegram_reports_enabled = (
            request.POST.get('telegram_reports_enabled') == 'on'
        )
        system_settings.telegram_bot_token = request.POST.get(
            'telegram_bot_token',
            ''
        ).strip() or None
        system_settings.telegram_chat_id = request.POST.get(
            'telegram_chat_id',
            ''
        ).strip() or None
        system_settings.telegram_report_time = (
            request.POST.get('telegram_report_time') or None
        )
        system_settings.save(
            update_fields=[
                'waiter_commission_percent',
                'waiter_daily_fixed_pay',
                'currency',
                'usd_to_base_rate',
                'rub_to_base_rate',
                'receipt_header',
                'receipt_footer',
                'receipt_show_waiter',
                'telegram_reports_enabled',
                'telegram_bot_token',
                'telegram_chat_id',
                'telegram_report_time',
                'updated_at'
            ]
        )
        messages.success(
            request,
            'POS settings saqlandi.'
        )

        return redirect(
            'settings_dashboard'
        )

    context = {

        'restaurant_count': Restaurant.objects.count(),

        'branch_count': Branch.objects.count(),

        'user_count': User.objects.count(),

        'product_count': Product.objects.count(),

        'menu_count': MenuItem.objects.count(),

        'supplier_count': Supplier.objects.count(),

        'purchase_count': Purchase.objects.count(),

        'settings_count': SystemSettings.objects.count(),

        'system_settings': system_settings,

    }

    return render(
        request,
        'settings/dashboard.html',
        context
    )


@permission_required(
    'settings',
    'edit'
)
def send_telegram_report_now(request):

    try:

        ok, message = send_daily_report()

    except Exception as exc:

        ok = False

        message = f'Telegram report yuborilmadi: {exc}'

    if ok:

        messages.success(request, 'Telegram report yuborildi.')

    else:

        messages.error(request, message)

    return redirect('settings_dashboard')


def _first_restaurant():

    return Restaurant.objects.order_by('id').first()


def _first_branch(restaurant=None):

    branches = Branch.objects.order_by('id')

    if restaurant:

        branches = branches.filter(restaurant=restaurant)

    return branches.first()


def _unique_slug(name):

    base_slug = slugify(name) or 'restaurant'
    slug = base_slug
    index = 2

    while Restaurant.objects.filter(slug=slug).exists():

        slug = f'{base_slug}-{index}'
        index += 1

    return slug


@permission_required(
    'settings',
    'create'
)
def admin_studio(request):

    section = request.GET.get('section') or request.POST.get('section') or 'restaurants'
    restaurants = Restaurant.objects.order_by('name')
    branches = Branch.objects.select_related('restaurant').order_by('name')
    roles = Role.objects.select_related('restaurant').order_by('name')
    suppliers = Supplier.objects.select_related('branch').order_by('name')
    products = Product.objects.select_related('branch').order_by('name')
    purchases = Purchase.objects.select_related('supplier').order_by('-created_at')[:8]
    combos = ComboMeal.objects.prefetch_related('items').order_by('name')
    menu_items = MenuItem.objects.order_by('name')

    if request.method == 'POST':

        form_type = request.POST.get('form_type')
        restaurant = _first_restaurant()
        branch = _first_branch(restaurant)

        if form_type == 'restaurant':

            name = request.POST.get('name', '').strip()

            if name:

                Restaurant.objects.create(
                    name=name,
                    slug=_unique_slug(name),
                    phone=request.POST.get('phone') or None,
                    email=request.POST.get('email') or None,
                    address=request.POST.get('address') or None,
                    currency=request.POST.get('currency') or 'UZS',
                    timezone=request.POST.get('timezone') or 'Asia/Tashkent',
                    language=request.POST.get('language') or 'uz',
                )
                messages.success(request, 'Restaurant qo‘shildi.')

        elif form_type == 'branch':

            restaurant = get_object_or_404(
                Restaurant,
                id=request.POST.get('restaurant')
            )
            Branch.objects.create(
                restaurant=restaurant,
                name=request.POST.get('name') or 'New Branch',
                address=request.POST.get('address') or None,
                phone=request.POST.get('phone') or None,
            )
            messages.success(request, 'Filial qo‘shildi.')

        elif form_type == 'role':

            restaurant = get_object_or_404(
                Restaurant,
                id=request.POST.get('restaurant')
            )
            Role.objects.create(
                restaurant=restaurant,
                name=request.POST.get('name') or 'New Role',
                description=request.POST.get('description') or None,
            )
            messages.success(request, 'Role qo‘shildi.')

        elif form_type == 'supplier':

            Supplier.objects.create(
                restaurant=restaurant,
                branch=branch,
                name=request.POST.get('name') or 'New Supplier',
                phone=request.POST.get('phone') or None,
                email=request.POST.get('email') or None,
                address=request.POST.get('address') or None,
            )
            messages.success(request, 'Supplier qo‘shildi.')

        elif form_type == 'product':

            Product.objects.create(
                restaurant=restaurant,
                branch=branch,
                name=request.POST.get('name') or 'New Product',
                quantity=float(request.POST.get('quantity') or 0),
                minimum_quantity=float(request.POST.get('minimum_quantity') or 5),
                unit=request.POST.get('unit') or 'pcs',
                cost_price=Decimal(request.POST.get('cost_price') or 0),
                barcode=request.POST.get('barcode') or None,
            )
            messages.success(request, 'Inventory product qo‘shildi.')

        elif form_type == 'purchase':

            supplier = get_object_or_404(
                Supplier,
                id=request.POST.get('supplier')
            )
            product = get_object_or_404(
                Product,
                id=request.POST.get('product')
            )
            purchase = Purchase.objects.create(
                restaurant=restaurant,
                branch=branch,
                supplier=supplier,
                invoice_number=request.POST.get('invoice_number') or f'PO-{Purchase.objects.count() + 1:05d}',
                due_date=request.POST.get('due_date') or None,
                notes=request.POST.get('notes') or None,
            )
            PurchaseItem.objects.create(
                purchase=purchase,
                product=product,
                quantity=float(request.POST.get('quantity') or 1),
                cost_price=Decimal(request.POST.get('cost_price') or product.cost_price),
            )
            purchase.save()
            messages.success(request, 'Purchase order yaratildi.')

        elif form_type == 'combo':

            combo = ComboMeal.objects.create(
                restaurant=restaurant,
                branch=branch,
                name=request.POST.get('name') or 'New Combo',
                price=Decimal(request.POST.get('price') or 0),
                fixed_price=Decimal(request.POST.get('fixed_price') or 0),
                discount_percent=Decimal(request.POST.get('discount_percent') or 0),
                description=request.POST.get('description') or None,
            )
            combo.items.set(
                MenuItem.objects.filter(
                    id__in=request.POST.getlist('items')
                )
            )
            messages.success(request, 'Combo menu qo‘shildi.')

        return redirect(
            f'/settings/studio/?section={section}'
        )

    context = {
        'section': section,
        'restaurants': restaurants,
        'branches': branches,
        'roles': roles,
        'suppliers': suppliers,
        'products': products,
        'purchases': purchases,
        'combos': combos,
        'menu_items': menu_items,
        'unit_choices': Product.UNIT_CHOICES,
    }

    return render(
        request,
        'settings/admin_studio.html',
        context
    )


@permission_required(
    'analytics',
    'view'
)
def accounting_dashboard(request):

    date_from = parse_date(
        request.GET.get('date_from') or ''
    )
    date_to = parse_date(
        request.GET.get('date_to') or ''
    )

    payments = Payment.objects.filter(status='paid')

    purchases_queryset = Purchase.objects.all()
    movements_queryset = CashMovement.objects.all()

    if date_from:

        payments = payments.filter(created_at__date__gte=date_from)
        purchases_queryset = purchases_queryset.filter(created_at__date__gte=date_from)
        movements_queryset = movements_queryset.filter(created_at__date__gte=date_from)

    if date_to:

        payments = payments.filter(created_at__date__lte=date_to)
        purchases_queryset = purchases_queryset.filter(created_at__date__lte=date_to)
        movements_queryset = movements_queryset.filter(created_at__date__lte=date_to)

    revenue = sum((payment.amount for payment in payments), Decimal('0'))
    purchases = sum(
        (purchase.total_amount for purchase in purchases_queryset),
        Decimal('0')
    )
    cash_in = sum(
        (
            movement.amount
            for movement in movements_queryset.filter(movement_type='in')
        ),
        Decimal('0')
    )
    cash_out = sum(
        (
            movement.amount
            for movement in movements_queryset.filter(movement_type='out')
        ),
        Decimal('0')
    )
    expenses = purchases + cash_out
    net_profit = revenue + cash_in - expenses

    method_rows = []

    for method, label in Payment.METHOD_CHOICES:

        method_rows.append(
            {
                'method': label,
                'total': sum(
                    (
                        payment.amount
                        for payment in payments.filter(method=method)
                    ),
                    Decimal('0')
                ),
            }
        )

    context = {
        'revenue': revenue,
        'purchases': purchases,
        'cash_in': cash_in,
        'cash_out': cash_out,
        'expenses': expenses,
        'net_profit': net_profit,
        'method_rows': method_rows,
        'recent_movements': CashMovement.objects.select_related(
            'shift',
            'created_by'
        ).filter(
            id__in=movements_queryset.values('id')
        ).order_by('-created_at')[:12],
        'recent_purchases': purchases_queryset.select_related(
            'supplier'
        ).order_by('-created_at')[:12],
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
    }

    return render(
        request,
        'settings/accounting_dashboard.html',
        context
    )


@permission_required(
    'analytics',
    'view'
)
def enterprise_dashboard(request):

    branches = Branch.objects.filter(
        active=True
    ).order_by(
        'name'
    )

    branch_rows = []

    for branch in branches:

        orders = Order.objects.filter(
            branch=branch
        )

        if not orders.exists():

            orders = Order.objects.filter(
                table__branch=branch
            )

        revenue = sum(
            (
                payment.amount
                for payment in Payment.objects.filter(
                    order__in=orders,
                    status='paid'
                )
            ),
            Decimal('0')
        )

        branch_rows.append(
            {
                'branch': branch,
                'orders': orders.count(),
                'revenue': revenue,
                'staff': User.objects.filter(branch=branch).count(),
                'tables': Table.objects.filter(branch=branch).count(),
                'stock_value': sum(
                    (
                        product.inventory_value
                        for product in Product.objects.filter(
                            branch=branch
                        )
                    ),
                    Decimal('0')
                ),
            }
        )

    return render(
        request,
        'settings/enterprise_dashboard.html',
        {
            'branch_rows': branch_rows,
            'total_revenue': sum(
                (row['revenue'] for row in branch_rows),
                Decimal('0')
            ),
            'total_orders': sum(row['orders'] for row in branch_rows),
            'total_staff': User.objects.count(),
            'total_branches': branches.count(),
        }
    )


@permission_required(
    'settings',
    'view'
)
def menu_management(request):

    if request.method == 'POST':

        restaurant = Restaurant.objects.first()
        branch_id = request.POST.get('branch')
        branch = (
            Branch.objects.filter(id=branch_id).first()
            if branch_id
            else Branch.objects.first()
        )

        try:

            price = Decimal(
                request.POST.get(
                    'price',
                    '0'
                ) or '0'
            )

        except Exception:

            price = Decimal('0')

        MenuItem.objects.create(
            restaurant=restaurant,
            branch=branch,
            name=request.POST.get('name', '').strip(),
            category=request.POST.get('category', 'main'),
            price=price,
            description=request.POST.get('description', '').strip(),
            preparation_time=int(
                request.POST.get(
                    'preparation_time',
                    '10'
                ) or 10
            ),
            available=bool(
                request.POST.get('available')
            ),
            is_spicy=bool(
                request.POST.get('is_spicy')
            ),
            is_vegetarian=bool(
                request.POST.get('is_vegetarian')
            ),
            available_from=request.POST.get(
                'available_from'
            ) or None,
            available_to=request.POST.get(
                'available_to'
            ) or None
        )

        messages.success(
            request,
            'Menu item added.'
        )

        return redirect(
            'menu_management'
        )

    menu_items = MenuItem.objects.select_related(
        'restaurant',
        'branch'
    ).order_by(
        'category',
        'name'
    )

    context = {

        'menu_items': menu_items,

        'branches': Branch.objects.order_by('name'),

        'categories': MenuItem.CATEGORY_CHOICES,

        'combo_count': ComboMeal.objects.count(),

        'available_count': menu_items.filter(
            available=True
        ).count(),

    }

    return render(
        request,
        'settings/menu_management.html',
        context
    )


@permission_required(
    'settings',
    'edit'
)
def toggle_menu_item_availability(request, item_id):

    item = get_object_or_404(
        MenuItem,
        id=item_id
    )
    item.available = not item.available
    item.save(
        update_fields=[
            'available',
            'updated_at'
        ]
    )

    messages.success(
        request,
        (
            f'{item.name} '
            f'{"enabled" if item.available else "stopped"}'
        )
    )

    return redirect(
        'menu_management'
    )


@permission_required(
    'settings',
    'view'
)
def staff_management(request):

    if request.method == 'POST':

        username = request.POST.get(
            'username',
            ''
        ).strip()

        if not username:

            messages.error(
                request,
                'Username required.'
            )

            return redirect(
                'staff_management'
            )

        if User.objects.filter(username=username).exists():

            messages.error(
                request,
                'Username already exists.'
            )

            return redirect(
                'staff_management'
            )

        restaurant = Restaurant.objects.first()
        branch = Branch.objects.filter(
            id=request.POST.get('branch')
        ).first() or Branch.objects.first()
        role = Role.objects.filter(
            id=request.POST.get('role')
        ).first()

        try:

            salary = Decimal(
                request.POST.get(
                    'salary',
                    '0'
                ) or '0'
            )

        except Exception:

            salary = Decimal('0')

        user = User.objects.create_user(
            username=username,
            password=request.POST.get(
                'password',
                '123456'
            ) or '123456',
            first_name=request.POST.get(
                'first_name',
                ''
            ).strip(),
            last_name=request.POST.get(
                'last_name',
                ''
            ).strip(),
            email=request.POST.get(
                'email',
                ''
            ).strip(),
            phone=request.POST.get(
                'phone',
                ''
            ).strip(),
            waiter_pin=request.POST.get(
                'waiter_pin',
                ''
            ).strip() or None,
            restaurant=restaurant,
            branch=branch,
            role=role,
            salary=salary,
            hire_date=request.POST.get(
                'hire_date'
            ) or None,
            birth_date=request.POST.get(
                'birth_date'
            ) or None,
            status=request.POST.get(
                'status',
                'active'
            ),
            is_staff=bool(
                request.POST.get('is_staff')
            )
        )

        if role:

            user.employee_id = f'BP-{user.id:04d}'
            user.save(
                update_fields=[
                    'employee_id'
                ]
            )

        messages.success(
            request,
            'Staff member added.'
        )

        return redirect(
            'staff_management'
        )

    staff = User.objects.select_related(
        'restaurant',
        'branch',
        'role'
    ).order_by(
        'role__name',
        'username'
    )

    context = {

        'staff': staff,

        'roles': Role.objects.order_by('name'),

        'branches': Branch.objects.order_by('name'),

        'active_count': staff.filter(
            status='active'
        ).count(),

        'manager_count': staff.filter(
            role__name__icontains='manager'
        ).count(),

        'waiter_count': staff.filter(
            role__name__icontains='waiter'
        ).count(),

    }

    return render(
        request,
        'settings/staff_management.html',
        context
    )


@permission_required(
    'analytics',
    'view'
)
def export_sales_excel(request):

    rows = [[
        'Payment ID',
        'Order ID',
        'Method',
        'Status',
        'Amount',
        'Created At',
    ]]

    for payment in Payment.objects.select_related(
        'order'
    ).order_by(
        '-created_at'
    )[:1000]:

        rows.append([
            payment.id,
            payment.order_id,
            payment.get_method_display(),
            payment.status,
            payment.amount,
            payment.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    response = HttpResponse(
        _build_simple_xlsx(rows),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=\"biteplate-sales.xlsx\"'

    return response
