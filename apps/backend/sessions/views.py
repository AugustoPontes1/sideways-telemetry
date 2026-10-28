from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import DrivingSession
from .serializers import DrivingSessionSerializer


class SessionListView(generics.ListAPIView):
    queryset = DrivingSession.objects.order_by("-last_sample_at")
    serializer_class = DrivingSessionSerializer
    permission_classes = [permissions.IsAdminUser]


class SessionDetailView(generics.RetrieveAPIView):
    queryset = DrivingSession.objects.all()
    serializer_class = DrivingSessionSerializer
    lookup_field = "stream_id"
    permission_classes = [permissions.IsAdminUser]


class TrackMapView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, stream_id):
        session = get_object_or_404(DrivingSession, pk=stream_id)
        track_map = session.track_map if (
            isinstance(session.track_map, dict)
            and isinstance(session.track_map.get("points"), list)
            and (
                len(session.track_map["points"]) >= 2
                or isinstance(session.track_map.get("image_url"), str)
            )
        ) else None
        return Response({
            "stream_id": str(session.stream_id),
            "track": session.track,
            "track_map": track_map,
        })


class PublicSessionListView(SessionListView):
    permission_classes = [permissions.AllowAny]


class PublicSessionDetailView(SessionDetailView):
    permission_classes = [permissions.AllowAny]


class PublicTrackMapView(TrackMapView):
    permission_classes = [permissions.AllowAny]
