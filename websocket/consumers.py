from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .models import User, Chat, Message
from asgiref.sync import async_to_sync
from .serializers import UserSerializer, MessageSerializer
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist


# Signal to listen to for notifying users about disconnection
@receiver(pre_delete, sender=User)
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
    # Delete the used chat for that user
    Chat.objects.filter(users__id=instance.id).delete()


# Whenever a user is created, create a chat room between him and every other one
@receiver(post_save, sender=User)
def create_chats(sender, instance, created, **kwargs):
    if created:
        for user in User.objects.exclude(id=instance.id):
            chat = Chat.objects.create()
            chat.users.set([user, instance])


class MainConsumer(AsyncJsonWebsocketConsumer):
    @staticmethod
    def create_user(username, uuid):
        user = User.objects.create_user(username, None, uuid=uuid)
        return user

    @staticmethod
    def delete_user(uuid):
        try:
            user = User.objects.get(uuid=uuid)
            user.delete()
        except ObjectDoesNotExist:
            pass

    @staticmethod
    def check_username(username):
        return User.objects.filter(username=username).exists()

    async def connect(self):
        # Create the user upon connection
        self.room_name = 'main'
        self.exception = False
        kwargs = self.scope['url_route']['kwargs']
        username = kwargs['username']
        uuid = kwargs['uuid']
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        await self.accept()
        exists = await database_sync_to_async(self.check_username)(username)
        if not exists:
            user = await database_sync_to_async(self.create_user)(username, uuid)
            # After the user is created, notify the other users!
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'send_event',
                    'payload': UserSerializer(user).data,
                    'ev': 'create'
                }
            )
        else:
            self.exception = True
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'send_event',
                    'payload': {
                        'message': 'This name is already taken..',
                        'uuid': uuid
                    },
                    'ev': 'exception'
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
        if not self.exception:
            await database_sync_to_async(self.delete_user)(uuid)
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['id']
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        await self.accept()

    @staticmethod
    def update_read(payload):
        chat_id = payload['chatId']
        sender_uuid = payload['uuid']
        Chat.objects.get(id=chat_id).messages.exclude(sender__uuid=sender_uuid).update(seen=True)

    @staticmethod
    def save_message(payload):
        uuid = payload['sender']['uuid']
        hash = payload['hash']
        chat_id = payload['chatId']
        text = payload.get('text')
        attachment = payload.get('attachment')
        if attachment is not None:
            attachment = bytes(attachment, encoding='utf-8')
        audio = payload.get('audio')
        if audio is not None:
            audio = bytes(audio, encoding='utf-8')
        user = User.objects.get(uuid=uuid)
        chat = Chat.objects.get(id=chat_id)
        message = Message.objects.create(hash=hash, sender=user, chat=chat, text=text,
                                         attachment=attachment, audio=audio)
        return message

    async def receive_json(self, content, **kwargs):
        typ = content['type']
        payload = content['payload']
        payload['chatId'] = self.scope['url_route']['kwargs']['id']
        if typ == 'read':
            await database_sync_to_async(self.update_read)(payload)
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'send_event',
                    'payload': {
                        'sender': {'uuid': payload['uuid']}
                    },
                    'ev': 'read'
                }
            )
        if typ == 'message':
            message = await database_sync_to_async(self.save_message)(payload)
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'send_event',
                    'payload': MessageSerializer(message).data,
                    'ev': 'message'
                }
            )
        if typ == 'rtc':
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'send_event',
                    'payload': payload,
                    'ev': 'rtc'
                }
            )

    async def send_event(self, event):
        ev = event['ev']
        payload = event['payload']
        data = {'type': ev, 'payload': payload}
        await self.send_json(content=data)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )
