from django.shortcuts import redirect

from django.http import HttpResponse


ROLE_ALIASES = {
    'chef': 'kitchen',
    'cook': 'kitchen',
    'oshpaz': 'kitchen',
    'server': 'waiter',
    'offitsiant': 'waiter',
    'stock manager': 'inventory',
    'inventory manager': 'inventory',
    'admin': 'manager',
}


# =====================================
# ROLE REQUIRED
# =====================================

def role_required(

    allowed_roles

):

    def decorator(view_func):

        def wrapper(

            request,
            *args,
            **kwargs

        ):

            user = request.user


            # =====================================
            # NOT AUTHENTICATED
            # =====================================

            if not user.is_authenticated:

                return redirect(
                    'login'
                )


            # =====================================
            # SUPERUSER ACCESS
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

                return HttpResponse(

                    'No role assigned'

                )


            # =====================================
            # ROLE NAME
            # =====================================

            role_name = str(

                user.role.name

            ).strip().lower()

            role_name = ROLE_ALIASES.get(
                role_name,
                role_name
            )


            # =====================================
            # NORMALIZE ROLES
            # =====================================

            normalized_roles = [

                ROLE_ALIASES.get(
                    str(role).strip().lower(),
                    str(role).strip().lower()
                )

                for role in allowed_roles

            ]


            # =====================================
            # ACCESS CHECK
            # =====================================

            if role_name not in normalized_roles:

                return HttpResponse(

                    f'Access Denied '

                    f'({role_name})'

                )


            return view_func(

                request,
                *args,
                **kwargs

            )

        return wrapper

    return decorator
