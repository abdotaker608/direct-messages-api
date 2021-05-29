from .models import User, Chat, Message
from rest_framework.serializers import ModelSerializer, ReadOnlyField, ModelField


class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'uuid', 'username']


class ChatSerializer(ModelSerializer):

    users = UserSerializer(many=True)
    last_message = ReadOnlyField()
    unread = ReadOnlyField()

    class Meta:
        model = Chat
        fields = '__all__'


class MessageSerializer(ModelSerializer):

    sender = UserSerializer()

    class Meta:
        model = Message
        fields = '__all__'
