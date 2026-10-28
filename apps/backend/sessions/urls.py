from django.urls import path
from .views import (
    PublicSessionDetailView,
    PublicSessionListView,
    PublicTrackMapView,
    SessionDetailView,
    SessionListView,
    TrackMapView,
)

urlpatterns = [
    path("public/sessions/", PublicSessionListView.as_view(), name="public-session-list"),
    path("public/sessions/<uuid:stream_id>/", PublicSessionDetailView.as_view(), name="public-session-detail"),
    path("public/sessions/<uuid:stream_id>/track-map/", PublicTrackMapView.as_view(), name="public-session-track-map"),
    path("sessions/", SessionListView.as_view(), name="session-list"),
    path("sessions/<uuid:stream_id>/", SessionDetailView.as_view(), name="session-detail"),
    path("sessions/<uuid:stream_id>/track-map/", TrackMapView.as_view(), name="session-track-map"),
]
