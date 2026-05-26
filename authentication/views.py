from django.shortcuts import render
from django.shortcuts import redirect

from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout


ROLE_REDIRECTS = {
    'admin': '/analytics/',
    'owner': '/analytics/',
    'manager': '/analytics/',
    'pos_admin': '/pos/',
    'cashier': '/cashier/',
    'waiter': '/waiter/',
    'server': '/waiter/',
    'offitsiant': '/waiter/',
    'kitchen': '/kitchen/',
    'chef': '/kitchen/',
    'cook': '/kitchen/',
    'oshpaz': '/kitchen/',
    'inventory manager': '/inventory-dashboard/',
    'stock manager': '/inventory-dashboard/',
    'accountant': '/settings/accounting/',
    'hr': '/staff/',
}


# =========================
# LOGIN
# =========================

def login_view(request):

    if request.user.is_authenticated:

        return role_redirect(
            request.user
        )

    error = None

    if request.method == 'POST':

        username = request.POST.get(
            'username'
        )

        password = request.POST.get(
            'password'
        )

        user = authenticate(

            request,

            username=username,

            password=password

        )

        if user is not None:

            login(request, user)

            return role_redirect(user)

        else:

            error = (

                'Invalid username '

                'or password'

            )

    context = {

        'error': error

    }

    return render(

        request,

        'authentication/login.html',

        context

    )


# =========================
# ROLE REDIRECT
# =========================

def role_redirect(user):

    # SUPERUSER
    if user.is_superuser:

        return redirect('/analytics/')

    if not user.role:

        return redirect('/logout/')

    role_name = str(
        user.role.name
    ).strip().lower()

    redirect_to = ROLE_REDIRECTS.get(
        role_name
    )

    if redirect_to:

        return redirect(redirect_to)

    return redirect('/analytics/')


# =========================
# LOGOUT
# =========================

def logout_view(request):

    logout(request)

    return redirect('/login/')
