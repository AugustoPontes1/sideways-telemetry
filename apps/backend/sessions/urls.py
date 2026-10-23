from django.urls import path
from .views import SessionDetailView, SessionListView

urlpatterns = [
    path("sessions/", SessionListView.as_view(), name="session-list"),
    path("sessions/<uuid:stream_id>/", SessionDetailView.as_view(), name="session-detail"),
]
