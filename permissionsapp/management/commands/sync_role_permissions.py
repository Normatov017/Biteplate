from django.core.management.base import BaseCommand

from permissionsapp.models import Permission
from permissionsapp.models import Role
from permissionsapp.models import RolePermission
from restaurants.models import Restaurant


MODULES = [
    'pos',
    'kitchen',
    'inventory',
    'billing',
    'hr',
    'analytics',
    'settings',
]

ACTIONS = [
    'view',
    'create',
    'edit',
    'delete',
    'approve',
]

ROLE_MATRIX = {
    'admin': 'all',
    'owner': 'all',
    'manager': 'all',
    'cashier': {
        'pos': ['view', 'create', 'edit'],
        'billing': ['view', 'create', 'edit', 'approve'],
        'analytics': ['view'],
    },
    'waiter': {
        'pos': ['view', 'create', 'edit'],
    },
    'server': {
        'pos': ['view', 'create', 'edit'],
    },
    'offitsiant': {
        'pos': ['view', 'create', 'edit'],
    },
    'chef': {
        'kitchen': ['view', 'edit'],
    },
    'kitchen': {
        'kitchen': ['view', 'edit'],
    },
    'cook': {
        'kitchen': ['view', 'edit'],
    },
    'oshpaz': {
        'kitchen': ['view', 'edit'],
    },
    'inventory manager': {
        'inventory': ['view', 'create', 'edit', 'approve'],
        'settings': ['view'],
    },
    'stock manager': {
        'inventory': ['view', 'create', 'edit', 'approve'],
        'settings': ['view'],
    },
    'accountant': {
        'billing': ['view', 'create', 'edit', 'approve'],
        'analytics': ['view'],
        'settings': ['view'],
    },
    'hr': {
        'hr': ['view', 'create', 'edit', 'approve'],
        'analytics': ['view'],
    },
}


class Command(BaseCommand):

    help = 'Create baseline permissions and sync permissions for known restaurant roles.'

    def handle(self, *args, **options):

        permissions = {}

        for module in MODULES:

            for action in ACTIONS:

                permission, _ = Permission.objects.get_or_create(
                    code=f'{module}.{action}',
                    defaults={
                        'module': module,
                        'action': action,
                    }
                )
                permissions[(module, action)] = permission

        restaurants = Restaurant.objects.all()
        synced = 0

        for restaurant in restaurants:

            for role_name in [
                'Admin',
                'Manager',
                'Cashier',
                'Waiter',
                'Chef',
                'Inventory Manager',
                'Accountant',
                'HR',
            ]:

                role, _ = Role.objects.get_or_create(
                    restaurant=restaurant,
                    name=role_name,
                    defaults={
                        'description': f'{role_name} access'
                    }
                )
                key = role.name.strip().lower()
                matrix = ROLE_MATRIX.get(key, {})

                if matrix == 'all':

                    allowed = list(
                        permissions.values()
                    )

                else:

                    allowed = [
                        permissions[(module, action)]
                        for module, actions in matrix.items()
                        for action in actions
                    ]

                RolePermission.objects.filter(
                    role=role
                ).exclude(
                    permission__in=allowed
                ).delete()

                for permission in allowed:

                    RolePermission.objects.get_or_create(
                        role=role,
                        permission=permission
                    )
                    synced += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Role permissions synced: {synced}'
            )
        )
