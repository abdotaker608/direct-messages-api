from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):

    uuid = models.CharField(max_length=500, unique=True)
    username = models.CharField(max_length=100, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['uuid']
    USERNAME_FIELD = "username"

    objects = UserManager()

    def __str__(self):
        return self.username


class Chat(models.Model):
    # Typically two users per chat
    users = models.ManyToManyField(User, related_name='chats')

    def __str__(self):
        return f"{self.users.first()} - {self.users.last()}"

    def last_message(self):
        from .serializers import MessageSerializer
        return MessageSerializer(self.messages.last()).data

    def unread(self):
        return self.messages.filter(seen=False).count()


class Message(models.Model):
    hash = models.CharField(max_length=500)
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)
    text = models.TextField(null=True, blank=True)
    audio = models.BinaryField(null=True, blank=True)
    attachment = models.BinaryField(null=True, blank=True)
    seen = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now=True)

    def get_attachment(self):
        if self.attachment is not None:
            return self.attachment.tobytes().decode()

    def get_audio(self):
        if self.audio is not None:
            return self.audio.tobytes().decode()

    class Meta:
        ordering = ('-created', )
