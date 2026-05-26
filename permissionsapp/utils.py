from django.http import HttpResponseForbidden

from django.shortcuts import redirect


ROLE_MODULE_ALIASES = {
    'waiter': {'waiter', 'server', 'offitsiant'},
    'tables': {'waiter', 'server', 'offitsiant', 'cashier', 'manager', 'owner', 'admin'},
    'kitchen': {'kitchen', 'chef', 'cook', 'oshpaz'},
    'orders': {'waiter', 'server', 'cashier', 'manager', 'owner', 'admin'},
    'pos': {'waiter', 'server', 'offitsiant', 'cashier', 'manager', 'owner', 'admin'},
    'display': {'kitchen', 'chef', 'cook', 'oshpaz', 'cashier', 'manager', 'owner', 'admin'},
    'billing': {'cashier', 'manager', 'owner', 'admin', 'accountant'},
    'inventory': {'inventory manager', 'stock manager', 'manager', 'owner', 'admin'},
    'hr': {'hr', 'manager', 'owner', 'admin'},
    'settings': {'manager', 'owner', 'admin'},
    'analytics': {'manager', 'owner', 'admin', 'accountant'},
}


def _role_can_access_module(user, module):

    role_name = str(user.role.name).strip().lower()
    return role_name in ROLE_MODULE_ALIASES.get(module, set())


# =====================================
# PERMISSION DECORATOR
# =====================================

def permission_required(

    module,
    action

):

    def decorator(view_func):

        def wrapper(

            request,
            *args,
            **kwargs

        ):

            user = request.user


            # =====================================
            # NOT LOGGED IN
            # =====================================

            if not user.is_authenticated:

                return redirect(
                    'login'
                )


            # =====================================
            # SUPERUSER
            # =====================================

            if user.is_superuser:

                return view_func(

                    request,
                    *args,
                    **kwargs

                )


            # =====================================
            # NO ROLE
            # =====================================

            if not hasattr(

                user,
                'role'

            ) or not user.role:

                return HttpResponseForbidden(

                    'No role assigned'

                )

            if _role_can_access_module(user, module):

                return view_func(

                    request,
                    *args,
                    **kwargs

                )


            # =====================================
            # PERMISSIONS
            # =====================================

            permissions = (

                user.role.permissions.all()

            )

            has_permission = False


            for role_permission in permissions:

                permission = (

                    role_permission.permission

                )

                if (

                    permission.module == module

                    and

                    permission.action == action

                ):

                    has_permission = True

                    break


            # =====================================
            # ACCESS DENIED
            # =====================================

            if not has_permission:

                return HttpResponseForbidden(

                    'Access Denied'

                )


            return view_func(

                request,
                *args,
                **kwargs

            )

        return wrapper

    return decorator



# =====================================
# HAS PERMISSION
# =====================================

def has_permission(

    user,
    module,
    action='view'

):

    if not user.is_authenticated:

        return False


    if user.is_superuser:

        return True


    if not hasattr(

        user,
        'role'

    ) or not user.role:

        return False

    if _role_can_access_module(user, module):

        return True


    permissions = (

        user.role.permissions.all()

    )

    for role_permission in permissions:

        permission = (

            role_permission.permission

        )

        if (

            permission.module == module

            and

            permission.action == action

        ):

            return True

    return False
