from django.urls import path

from .views import inventory_dashboard

urlpatterns = [

    path(
    'inventory-dashboard/',
    inventory_dashboard,
    name='inventory_dashboard'
    ),

]