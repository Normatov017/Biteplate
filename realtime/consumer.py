from channels.generic.websocket import AsyncWebsocketConsumer

import json


class OrderConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.room_group_name = 'orders'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        print("WEBSOCKET CONNECTED")


    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        print("WEBSOCKET DISCONNECTED")


    async def receive(self, text_data):

        pass


    async def send_update(self, event):

        message = event['message']

        await self.send(text_data=json.dumps({

            'message': message

        }))