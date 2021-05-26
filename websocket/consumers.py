from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .models import User
from asgiref.sync import async_to_sync
from .serializers import UserSerializer
from django.dispatch import receiver
from django.db.models.signals import post_delete
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async


# Signal to listen to for notifying users about disconnection
@receiver(post_delete, sender=User)
def notify_disconnect(sender, instance, **kwargs):
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        'main',
        {
            'type': 'send_event',
            'payload': UserSerializer(instance).data,
            'ev': 'delete'
        }
    )


class MainConsumer(AsyncJsonWebsocketConsumer):
    @staticmethod
    def create_user(username, uuid):
        user = User.objects.create_user(username, None, uuid=uuid)
        return user

    @staticmethod
    def delete_user(uuid):
        user = User.objects.get(uuid=uuid)
        user.delete()

    async def connect(self):
        # Create the user upon connection
        self.room_name = 'main'
        kwargs = self.scope['url_route']['kwargs']
        username = kwargs['username']
        uuid = kwargs['uuid']
        user = await database_sync_to_async(self.create_user)(username, uuid)
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        await self.accept()
        # After the user is created, notify the other users!
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'send_event',
                'payload': UserSerializer(user).data,
                'ev': 'create'
            }
        )

    async def send_event(self, event):
        data = {
            'type': event['ev'],
            'payload': event['payload'],
        }
        await self.send_json(content=data)

    async def disconnect(self, code):
        # Delete the user upon disconnection
        uuid = self.scope['url_route']['kwargs']['uuid']
        await database_sync_to_async(self.delete_user)(uuid)
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

