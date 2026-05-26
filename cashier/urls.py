from django.urls import path

from .views import cashier_dashboard


urlpatterns = [

    path(
        '',
        cashier_dashboard,
        name='cashier_dashboard'
    ),

]