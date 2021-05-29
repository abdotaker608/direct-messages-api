from rest_framework import generics, mixins
from .serializers import ChatSerializer, MessageSerializer
from .models import Chat, Message
import datetime


class ChatsView(generics.GenericAPIView, mixins.ListModelMixin):

    serializer_class = ChatSerializer

    def get(self, request):
        return self.list(request)

    def get_queryset(self):
        uuid = self.request.query_params.get('uuid')
        return Chat.objects.filter(users__uuid=uuid)


class MessageView(generics.GenericAPIView, mixins.ListModelMixin):

    serializer_class = MessageSerializer

    def get(self, request, pk):
        return self.list(request)

    def get_queryset(self):
        chat_id = self.kwargs['pk']
        last_date = self.request.query_params.get('lastDate')
        chat = Chat.objects.get(id=chat_id)
        if last_date is not None:
            rang = datetime.datetime.strptime(last_date, '%Y-%m-%dT%H:%M:%S.%fZ')
            last_date = last_date.replace('Z', '+00:00').replace('T', ' ')
            messages = chat.messages.exclude(created=last_date).filter(created__lt=rang)[:20]
        else:
            messages = chat.messages.all()[:20]
        return reversed(messages)
