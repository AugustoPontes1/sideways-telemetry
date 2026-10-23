"""ASGI: HTTP Django, WebSocket de ingestão e leitura ao vivo."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.asgi import get_asgi_application

# Popula o registro dos aplicativos antes de importar consumers que usam models.
django_application = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path

from telemetry.consumers import IngestConsumer, SessionLiveConsumer

application = ProtocolTypeRouter({
    "http": django_application,
    "websocket": URLRouter([
        # Cliente não-browser usa Authorization: Bearer, sem Origin.
        path("ws/ingest/", IngestConsumer.as_asgi()),
        # Browser usa cookie de sessão Django e checagem de Origin.
        path("ws/sessions/<uuid:stream_id>/live/",
             AllowedHostsOriginValidator(AuthMiddlewareStack(SessionLiveConsumer.as_asgi()))),
    ]),
})
