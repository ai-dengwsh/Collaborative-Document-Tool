from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.documents.consumers import DocumentConsumer

websocket_urlpatterns = [
    re_path(r'ws/documents/(?P<document_id>\w+)/$', DocumentConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
