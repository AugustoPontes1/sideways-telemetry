import uuid

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from sessions.models import DrivingSession
from telemetry.models import TelemetrySample
from .reference import compare_with_reference
from .services import summarize_session


class SessionAnalysisView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, stream_id):
        session = get_object_or_404(DrivingSession, pk=stream_id)
        return Response(summarize_session(session))


class TrajectoryComparisonView(APIView):
    """Compare a recent window with a reference capture from the SAME track."""
    permission_classes = [IsAdminUser]

    def get(self, request, stream_id):
        session = get_object_or_404(DrivingSession, pk=stream_id)
        reference_raw = request.query_params.get("reference", "")
        try:
            reference_id = uuid.UUID(reference_raw)
        except (TypeError, ValueError, AttributeError):
            return Response({"detail": "Informe ?reference=<uuid-da-sessao>"}, status=400)
        if reference_id == stream_id:
            return Response({"detail": "Escolha uma captura diferente como referência"}, status=400)
        reference = get_object_or_404(DrivingSession, pk=reference_id)
        if session.track != reference.track:
            return Response({"detail": "Comparações exigem a mesma pista"}, status=400)

        def last_positions(stream):
            # Last 2,000 points; light decimation to limit computational cost.
            rows = list(TelemetrySample.objects.filter(session=stream)
                        .order_by("-sequence").values_list("position_world_m", flat=True)[:2000])
            rows.reverse()
            stride = max(1, (len(rows) + 499) // 500)
            return rows[::stride]

        current_path, reference_path = last_positions(session), last_positions(reference)
        if not current_path or not reference_path:
            return Response({"detail": "São necessárias amostras nas duas sessões"}, status=400)
        output = compare_with_reference(current_path, reference_path)
        output["current_stream_id"] = str(stream_id)
        output["reference_stream_id"] = str(reference_id)
        return Response(output)
