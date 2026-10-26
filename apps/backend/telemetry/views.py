"""Paginated API for feeding 2D plots and 3D replays."""
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from sessions.models import DrivingSession
from .models import TelemetrySample
from .serializers import TelemetrySampleSerializer


class SessionSamplesView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, stream_id):
        get_object_or_404(DrivingSession, pk=stream_id)
        try:
            limit = int(request.query_params.get("limit", "250"))
            after = int(request.query_params.get("after", "-1"))
            if not 1 <= limit <= 1000 or after < -1:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"detail": "limit (1..1000) ou after (>=-1) inválido"}, status=400)
        samples = list(TelemetrySample.objects.filter(
            session_id=stream_id, sequence__gt=after
        ).order_by("sequence")[: limit + 1])
        has_more = len(samples) > limit
        page = samples[:limit]
        return Response({
            "stream_id": str(stream_id),
            "samples": TelemetrySampleSerializer(page, many=True).data,
            "has_more": has_more,
            "next_after": page[-1].sequence if page else None,
        })
