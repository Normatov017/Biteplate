from django.shortcuts import render
from django.shortcuts import redirect

from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout


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

        return redirect('/login/')

    role_name = user.role.name.lower()


    # WAITER
    if role_name == 'waiter':

        return redirect('/waiter/')


    # KITCHEN
    elif role_name == 'kitchen':

        return redirect('/kitchen/')


    # CASHIER
    elif role_name == 'cashier':

        return redirect('/cashier/')


    # POS ADMIN
    elif role_name == 'pos_admin':

        return redirect('/pos/')


    # MANAGER
    elif role_name == 'manager':

        return redirect('/analytics/')


    # OWNER
    elif role_name == 'owner':

        return redirect('/analytics/')


    return redirect('/')


# =========================
# LOGOUT
# =========================

def logout_view(request):

    logout(request)

    return redirect('/login/')