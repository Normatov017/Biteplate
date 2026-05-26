from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from inventory.models import (
    Product,
    Purchase,
    PurchaseItem,
    RecipeIngredient,
    Supplier
)
from menu.models import (
    ComboMeal,
    MenuItem,
    ModifierGroup,
    ModifierOption,
    ProductVariant,
    SingleMenuItem
)
from orders.models import Table
from permissionsapp.models import Permission, Role, RolePermission
from restaurants.models import Branch, Restaurant
from settingsapp.models import SystemSettings


class Command(BaseCommand):

    help = 'Seed BitePlate with restaurant, branches, staff, menu, inventory and purchases.'

    def handle(self, *args, **options):

        restaurant, _ = Restaurant.objects.get_or_create(
            slug='biteplate-demo',
            defaults={
                'name': 'BitePlate Demo Restaurant',
                'phone': '+998 90 100 10 10',
                'email': 'demo@biteplate.local',
                'address': 'Tashkent City, Food Street 12',
                'currency': 'UZS',
                'timezone': 'Asia/Tashkent',
                'language': 'uz',
                'active': True
            }
        )

        branches = {}

        for name, address, phone in [
            ('Main Branch', 'Tashkent, City Center', '+998 90 111 11 11'),
            ('Yunusabad Branch', 'Tashkent, Yunusabad 7', '+998 90 222 22 22'),
            ('Samarqand Branch', 'Samarqand, Registon area', '+998 90 333 33 33'),
        ]:
            branch, _ = Branch.objects.get_or_create(
                restaurant=restaurant,
                name=name,
                defaults={
                    'address': address,
                    'phone': phone,
                    'active': True
                }
            )
            branches[name] = branch

        main_branch = branches['Main Branch']

        SystemSettings.objects.get_or_create(
            restaurant=restaurant,
            branch=main_branch,
            defaults={
                'tax_percent': Decimal('0'),
                'service_fee_percent': Decimal('10'),
                'enable_qr_menu': True,
                'auto_inventory_deduction': True,
                'auto_send_kitchen': True
            }
        )

        for table_number in range(1, 13):
            Table.objects.get_or_create(
                restaurant=restaurant,
                branch=main_branch,
                table_number=table_number,
                defaults={
                    'seats': 2 + (table_number % 4) * 2,
                    'status': 'free',
                    'assigned_waiter': 'Ali'
                }
            )

        permissions = []

        for module in [
            'pos',
            'kitchen',
            'inventory',
            'billing',
            'hr',
            'analytics',
            'settings'
        ]:
            for action in [
                'view',
                'create',
                'edit',
                'delete',
                'approve'
            ]:
                permission, _ = Permission.objects.get_or_create(
                    code=f'{module}.{action}',
                    defaults={
                        'module': module,
                        'action': action
                    }
                )
                permissions.append(permission)

        role_names = {
            'Admin': 'Full system access',
            'Manager': 'Branch manager',
            'Cashier': 'Checkout and payments',
            'Waiter': 'Tables and dine-in orders',
            'Chef': 'Kitchen display and preparation',
            'Inventory Manager': 'Stock, suppliers and purchases'
        }

        roles = {}

        for name, description in role_names.items():
            role, _ = Role.objects.get_or_create(
                restaurant=restaurant,
                name=name,
                defaults={
                    'description': description
                }
            )
            roles[name] = role

        for role_name, role in roles.items():
            allowed_permissions = permissions

            if role_name == 'Waiter':
                allowed_permissions = [
                    permission
                    for permission in permissions
                    if permission.module in ['pos', 'billing']
                    and permission.action in ['view', 'create', 'edit']
                ]

            if role_name == 'Chef':
                allowed_permissions = [
                    permission
                    for permission in permissions
                    if permission.module == 'kitchen'
                    and permission.action in ['view', 'edit']
                ]

            if role_name == 'Cashier':
                allowed_permissions = [
                    permission
                    for permission in permissions
                    if permission.module in ['pos', 'billing']
                    and permission.action in ['view', 'create', 'edit', 'approve']
                ]

            if role_name == 'Inventory Manager':
                allowed_permissions = [
                    permission
                    for permission in permissions
                    if permission.module == 'inventory'
                    or permission.module == 'settings'
                    and permission.action == 'view'
                ]

            for permission in allowed_permissions:
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=permission
                )

        staff_rows = [
            ('admin_demo', 'Admin', 'Demo', 'Admin', '+998901000001', 'BP-001', Decimal('12000000'), True, True),
            ('manager_demo', 'Manager', 'Aziz', 'Karimov', '+998901000002', 'BP-002', Decimal('9000000'), True, False),
            ('cashier_demo', 'Cashier', 'Malika', 'Rasulova', '+998901000003', 'BP-003', Decimal('6000000'), True, False),
            ('waiter_ali', 'Waiter', 'Ali', 'Nazarov', '+998901000004', 'BP-004', Decimal('4500000'), False, False),
            ('waiter_dilnoza', 'Waiter', 'Dilnoza', 'Saidova', '+998901000005', 'BP-005', Decimal('4500000'), False, False),
            ('chef_jamshid', 'Chef', 'Jamshid', 'Usmonov', '+998901000006', 'BP-006', Decimal('7000000'), False, False),
            ('chef_madina', 'Chef', 'Madina', 'Tursunova', '+998901000007', 'BP-007', Decimal('6800000'), False, False),
            ('stock_bek', 'Inventory Manager', 'Bekzod', 'Murodov', '+998901000008', 'BP-008', Decimal('6500000'), False, False),
        ]

        for username, role_name, first_name, last_name, phone, employee_id, salary, is_staff, is_superuser in staff_rows:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': f'{username}@biteplate.local',
                    'phone': phone,
                    'employee_id': employee_id,
                    'restaurant': restaurant,
                    'branch': main_branch,
                    'role': roles[role_name],
                    'salary': salary,
                    'hire_date': timezone.now().date(),
                    'status': 'active',
                    'is_staff': is_staff,
                    'is_superuser': is_superuser
                }
            )

            if created:
                user.set_password('123456')
                user.save()
            else:
                User.objects.filter(id=user.id).update(
                    restaurant=restaurant,
                    branch=main_branch,
                    role=roles[role_name],
                    status='active'
                )

        supplier_rows = [
            ('Fresh Farm Market', '+998 90 444 44 44', 'fresh@suppliers.local'),
            ('Metro Food Supply', '+998 90 555 55 55', 'metro@suppliers.local'),
            ('Beverage House', '+998 90 666 66 66', 'drinks@suppliers.local'),
        ]

        suppliers = {}

        for name, phone, email in supplier_rows:
            supplier, _ = Supplier.objects.get_or_create(
                restaurant=restaurant,
                branch=main_branch,
                name=name,
                defaults={
                    'phone': phone,
                    'email': email,
                    'address': 'Tashkent wholesale market'
                }
            )
            suppliers[name] = supplier

        product_rows = [
            ('Beef Patty', 35, 8, 'kg', Decimal('72000')),
            ('Chicken Fillet', 28, 6, 'kg', Decimal('48000')),
            ('Burger Bun', 180, 40, 'pcs', Decimal('2500')),
            ('Mozzarella Cheese', 22, 5, 'kg', Decimal('65000')),
            ('Tomato', 40, 8, 'kg', Decimal('12000')),
            ('Lettuce', 18, 4, 'kg', Decimal('18000')),
            ('Potato', 80, 15, 'kg', Decimal('8000')),
            ('Pizza Dough', 90, 20, 'pcs', Decimal('6000')),
            ('Pasta', 45, 10, 'kg', Decimal('18000')),
            ('Rice', 60, 12, 'kg', Decimal('14000')),
            ('Coca-Cola 0.5', 120, 24, 'pcs', Decimal('6500')),
            ('Water 0.5', 150, 30, 'pcs', Decimal('2500')),
            ('Coffee Beans', 12, 3, 'kg', Decimal('90000')),
            ('Tea Leaves', 8, 2, 'kg', Decimal('52000')),
        ]

        products = {}

        for name, quantity, minimum, unit, cost_price in product_rows:
            product, _ = Product.objects.get_or_create(
                restaurant=restaurant,
                branch=main_branch,
                name=name,
                defaults={
                    'quantity': quantity,
                    'minimum_quantity': minimum,
                    'unit': unit,
                    'cost_price': cost_price
                }
            )
            products[name] = product

        menu_rows = [
            ('Classic Burger', 'fast_food', Decimal('35000'), 'Beef patty, cheese, tomato and sauce.', 12, False, False),
            ('Cheese Burger', 'fast_food', Decimal('42000'), 'Double cheese and grilled beef.', 14, False, False),
            ('Chicken Burger', 'fast_food', Decimal('39000'), 'Crispy chicken, lettuce and garlic sauce.', 12, False, False),
            ('Margherita Pizza', 'main', Decimal('62000'), 'Tomato sauce, mozzarella and basil.', 18, False, True),
            ('Pepperoni Pizza', 'main', Decimal('78000'), 'Pepperoni, mozzarella and tomato sauce.', 20, True, False),
            ('Chicken Alfredo Pasta', 'main', Decimal('64000'), 'Creamy pasta with chicken fillet.', 16, False, False),
            ('Bolognese Pasta', 'main', Decimal('67000'), 'Beef sauce and parmesan.', 18, False, False),
            ('Caesar Salad', 'starter', Decimal('38000'), 'Fresh lettuce, chicken, croutons and sauce.', 9, False, False),
            ('Greek Salad', 'starter', Decimal('34000'), 'Tomato, cucumber, feta and olives.', 8, False, True),
            ('French Fries', 'starter', Decimal('22000'), 'Crispy potato fries.', 7, False, True),
            ('Chicken Plov', 'main', Decimal('52000'), 'Rice, chicken, carrot and spices.', 15, False, False),
            ('Beef Steak', 'main', Decimal('115000'), 'Grilled beef steak with potato side.', 22, False, False),
            ('Sushi Set', 'main', Decimal('99000'), 'Mixed rolls and soy sauce.', 18, False, False),
            ('Chocolate Cake', 'dessert', Decimal('32000'), 'Rich chocolate slice.', 6, False, True),
            ('Cheesecake', 'dessert', Decimal('36000'), 'Creamy cheesecake with berry sauce.', 6, False, True),
            ('Coca-Cola', 'beverage', Decimal('12000'), 'Cold Coca-Cola 0.5L.', 1, False, True),
            ('Still Water', 'beverage', Decimal('6000'), 'Water 0.5L.', 1, False, True),
            ('Espresso', 'beverage', Decimal('18000'), 'Fresh espresso shot.', 4, False, True),
            ('Green Tea', 'beverage', Decimal('12000'), 'Hot green tea pot.', 5, False, True),
            ('Berry Lemonade', 'beverage', Decimal('24000'), 'Fresh berry lemonade.', 5, False, True),
        ]

        menu_items = {}

        for name, category, price, description, prep_time, is_spicy, is_vegetarian in menu_rows:
            item, _ = MenuItem.objects.get_or_create(
                restaurant=restaurant,
                branch=main_branch,
                name=name,
                defaults={
                    'category': category,
                    'price': price,
                    'description': description,
                    'preparation_time': prep_time,
                    'is_spicy': is_spicy,
                    'is_vegetarian': is_vegetarian,
                    'available': True
                }
            )
            menu_items[name] = item
            SingleMenuItem.objects.get_or_create(
                menu_item=item,
                defaults={
                    'name': item.name,
                    'price': item.price
                }
            )

        cheese_group, _ = ModifierGroup.objects.get_or_create(
            restaurant=restaurant,
            branch=main_branch,
            name='Extras',
            defaults={
                'required': False,
                'multiple_choice': True
            }
        )

        for name, price in [
            ('Extra Cheese', Decimal('6000')),
            ('No Onion', Decimal('0')),
            ('Spicy Sauce', Decimal('3000')),
            ('Double Meat', Decimal('18000')),
            ('Allergy: Nuts', Decimal('0')),
        ]:
            ModifierOption.objects.get_or_create(
                group=cheese_group,
                name=name,
                defaults={
                    'extra_price': price
                }
            )

        for item_name in [
            'Classic Burger',
            'Cheese Burger',
            'Chicken Burger',
            'Margherita Pizza',
            'Pepperoni Pizza'
        ]:
            menu_items[item_name].modifier_groups.add(cheese_group)

        for item_name in [
            'Classic Burger',
            'Cheese Burger',
            'Chicken Burger'
        ]:
            for variant_name, extra_price in [
                ('Regular', Decimal('0')),
                ('Double', Decimal('18000')),
                ('Combo Size', Decimal('24000')),
            ]:
                ProductVariant.objects.get_or_create(
                    menu_item=menu_items[item_name],
                    name=variant_name,
                    defaults={
                        'extra_price': extra_price,
                        'available': True
                    }
                )

        recipe_rows = [
            ('Classic Burger', 'Beef Patty', 0.18),
            ('Classic Burger', 'Burger Bun', 1),
            ('Classic Burger', 'Mozzarella Cheese', 0.03),
            ('Cheese Burger', 'Beef Patty', 0.18),
            ('Cheese Burger', 'Burger Bun', 1),
            ('Cheese Burger', 'Mozzarella Cheese', 0.06),
            ('Chicken Burger', 'Chicken Fillet', 0.16),
            ('Chicken Burger', 'Burger Bun', 1),
            ('French Fries', 'Potato', 0.22),
            ('Margherita Pizza', 'Pizza Dough', 1),
            ('Margherita Pizza', 'Mozzarella Cheese', 0.12),
            ('Chicken Alfredo Pasta', 'Pasta', 0.14),
            ('Chicken Alfredo Pasta', 'Chicken Fillet', 0.12),
            ('Chicken Plov', 'Rice', 0.18),
            ('Chicken Plov', 'Chicken Fillet', 0.14),
            ('Coca-Cola', 'Coca-Cola 0.5', 1),
            ('Still Water', 'Water 0.5', 1),
            ('Espresso', 'Coffee Beans', 0.018),
            ('Green Tea', 'Tea Leaves', 0.012),
        ]

        for item_name, product_name, quantity in recipe_rows:
            RecipeIngredient.objects.get_or_create(
                menu_item=menu_items[item_name],
                product=products[product_name],
                defaults={
                    'quantity_required': quantity
                }
            )

        combo_rows = [
            ('Burger Combo', Decimal('15'), ['Classic Burger', 'French Fries', 'Coca-Cola']),
            ('Pizza Party', Decimal('10'), ['Margherita Pizza', 'Caesar Salad', 'Berry Lemonade']),
            ('Lunch Set', Decimal('12'), ['Chicken Plov', 'Greek Salad', 'Green Tea']),
        ]

        for combo_name, discount, item_names in combo_rows:
            combo, _ = ComboMeal.objects.get_or_create(
                restaurant=restaurant,
                branch=main_branch,
                name=combo_name,
                defaults={
                    'price': Decimal('0'),
                    'description': 'Auto priced bundle with discount.',
                    'discount_percent': discount,
                    'is_active': True
                }
            )
            combo.items.set(
                [
                    menu_items[item_name]
                    for item_name in item_names
                ]
            )
            combo.price = combo.get_total_price()
            combo.save()

        purchase, _ = Purchase.objects.get_or_create(
            restaurant=restaurant,
            branch=main_branch,
            invoice_number='DEMO-PO-001',
            defaults={
                'supplier': suppliers['Fresh Farm Market'],
                'status': 'draft',
                'notes': 'Demo opening purchase.'
            }
        )

        for product_name in [
            'Beef Patty',
            'Chicken Fillet',
            'Burger Bun',
            'Tomato',
            'Lettuce'
        ]:
            PurchaseItem.objects.get_or_create(
                purchase=purchase,
                product=products[product_name],
                defaults={
                    'quantity': 10,
                    'cost_price': products[product_name].cost_price
                }
            )

        purchase.save()

        self.stdout.write(
            self.style.SUCCESS(
                'Sample data ready: restaurant, branches, staff, menu, inventory, recipes, combo and purchase.'
            )
        )
