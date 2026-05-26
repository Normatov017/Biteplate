from permissionsapp.utils import has_permission


# =====================================
# SIDEBAR PERMISSIONS
# =====================================

def sidebar_permissions(request):

    user = request.user

    if not user.is_authenticated:

        return {}

    role_name = ''

    if hasattr(user, 'role') and user.role:

        role_name = str(user.role.name).strip().lower()

    if role_name in {'waiter', 'server', 'offitsiant'}:

        return {
            'can_view_pos': True,
            'can_view_waiter': True,
            'can_view_inventory': False,
            'can_view_kitchen': False,
            'can_view_billing': False,
            'can_view_hr': False,
            'can_view_analytics': False,
            'can_view_settings': False,
        }

    if role_name in {'kitchen', 'chef', 'cook', 'oshpaz'}:

        return {
            'can_view_pos': False,
            'can_view_waiter': False,
            'can_view_inventory': False,
            'can_view_kitchen': True,
            'can_view_billing': False,
            'can_view_hr': False,
            'can_view_analytics': False,
            'can_view_settings': False,
        }

    if role_name == 'cashier':

        return {
            'can_view_pos': True,
            'can_view_waiter': False,
            'can_view_inventory': False,
            'can_view_kitchen': False,
            'can_view_billing': True,
            'can_view_hr': False,
            'can_view_analytics': False,
            'can_view_settings': False,
        }


    return {

        'can_view_pos': has_permission(
            user,
            'pos'
        ),

        'can_view_waiter': has_permission(
            user,
            'waiter'
        ),

        'can_view_inventory': has_permission(
            user,
            'inventory'
        ),

        'can_view_kitchen': has_permission(
            user,
            'kitchen'
        ),

        'can_view_billing': has_permission(
            user,
            'billing'
        ),

        'can_view_hr': has_permission(
            user,
            'hr'
        ),

        'can_view_analytics': has_permission(
            user,
            'analytics'
        ),

        'can_view_settings': has_permission(
            user,
            'settings'
        ),

    }
