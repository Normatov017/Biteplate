from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer


def send_order_update(message):

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(

        'orders',

        {
            'type': 'send_update',
            'message': message
        }

    )   