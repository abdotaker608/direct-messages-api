from django.urls import re_path
from . import consumers

routes = [
    re_path(r'^websocket/main/(?P<uuid>[a-z0-9-]+)/(?P<username>[\w\s]+)$', consumers.MainConsumer.as_asgi())
]