from rest_framework import generics, permissions
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
