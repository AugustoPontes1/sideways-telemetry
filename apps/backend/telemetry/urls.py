from django.urls import path
from .views import PublicSessionSamplesView, SessionSamplesView

urlpatterns = [
    path("public/sessions/<uuid:stream_id>/samples/", PublicSessionSamplesView.as_view(), name="public-session-samples"),
    path("sessions/<uuid:stream_id>/samples/", SessionSamplesView.as_view(), name="session-samples"),
]
