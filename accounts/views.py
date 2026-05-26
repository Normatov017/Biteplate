from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout


ROLE_REDIRECTS = {
    'waiter': '/waiter/',
    'server': '/waiter/',
    'offitsiant': '/waiter/',
    'kitchen': '/kitchen/',
    'chef': '/kitchen/',
    'cook': '/kitchen/',
    'oshpaz': '/kitchen/',
    'cashier': '/cashier/',
    'inventory manager': '/inventory/',
    'stock manager': '/inventory/',
    'accountant': '/settings/accounting/',
    'manager': '/',
    'owner': '/',
    'admin': '/',
}


def get_role_redirect(user):

    if user.is_superuser:

        return '/'

    role = getattr(user, 'role', None)

    role_name = getattr(role, 'name', '')

    role_name = str(role_name).strip().lower()

    return ROLE_REDIRECTS.get(role_name, '/')


# =========================
# LOGIN
# =========================

def login_view(request):

    error = None

    if request.method == 'POST':

        username = request.POST.get('username')

        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:

            login(request, user)

            return redirect(get_role_redirect(user))

        else:

            error = 'Invalid username or password'

    context = {
        'error': error
    }

    return render(
        request,
        'login.html',
        context
    )


# =========================
# LOGOUT
# =========================

def logout_view(request):

    logout(request)

    return redirect('/login/')
