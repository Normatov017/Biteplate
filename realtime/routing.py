from django.urls import path

from .consumer import OrderConsumer


websocket_urlpatterns = [

    path(
        'ws/orders/',
        OrderConsumer.as_asgi()
    ),

]