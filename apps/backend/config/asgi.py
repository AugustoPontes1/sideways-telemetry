"""ASGI: Django HTTP, WebSocket ingestion, and live reads."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.asgi import get_asgi_application

# Populate the app registry before importing consumers that use models.
django_application = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path

from telemetry.consumers import IngestConsumer, SessionLiveConsumer

application = ProtocolTypeRouter({
    "http": django_application,
    "websocket": URLRouter([
        # Non-browser clients use Authorization: Bearer without an Origin.
        path("ws/ingest/", IngestConsumer.as_asgi()),
        # Browsers use the Django session cookie and an Origin check.
        path("ws/sessions/<uuid:stream_id>/live/",
             AllowedHostsOriginValidator(AuthMiddlewareStack(SessionLiveConsumer.as_asgi()))),
    ]),
})
