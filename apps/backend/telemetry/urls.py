from django.urls import path
from .views import SessionSamplesView

urlpatterns = [
    path("sessions/<uuid:stream_id>/samples/", SessionSamplesView.as_view(), name="session-samples"),
]
