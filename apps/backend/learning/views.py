"""API do Modo Estudo: solução só aparece em reveal=1."""
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from sessions.models import DrivingSession
from telemetry.models import TelemetrySample
from .services import TOPICS, ExerciseUnavailable, compare_answer, generate_exercise


def locate_samples(session, query):
    """Se não vierem índices, usa as duas amostras mais recentes."""
    first_raw, second_raw = query.get("a"), query.get("b")
    if (first_raw is None) != (second_raw is None):
        raise ExerciseUnavailable("Informe ambos a e b, ou nenhum")
    qs = TelemetrySample.objects.filter(session=session)
    if first_raw is None:
        points = list(qs.order_by("-sequence")[:2])
        if len(points) < 2:
            raise ExerciseUnavailable("A sessão precisa ter pelo menos duas amostras")
        return points[1], points[0]
    try:
        first_seq, second_seq = int(first_raw), int(second_raw)
    except (ValueError, TypeError) as exc:
        raise ExerciseUnavailable("a e b precisam ser sequências inteiras") from exc
    if min(first_seq, second_seq) < 0 or first_seq == second_seq:
        raise ExerciseUnavailable("a e b precisam ser sequências distintas não negativas")
    first = qs.filter(sequence=first_seq).first()
    second = qs.filter(sequence=second_seq).first()
    if not first or not second:
        raise ExerciseUnavailable("Uma das amostras não existe nesta sessão")
    return first, second


class ExerciseTopicsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({"topics": [dict(id=key, **value) for key, value in TOPICS.items()]})


class SessionExerciseView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, stream_id):
        session = get_object_or_404(DrivingSession, pk=stream_id)
        topic = request.query_params.get("topic", "displacement")
        reveal = request.query_params.get("reveal") in ("1", "true", "yes")
        try:
            a, b = locate_samples(session, request.query_params)
            exercise = generate_exercise(topic, a, b, reveal=reveal)
        except ExerciseUnavailable as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(exercise)


class SessionCheckAnswerView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, stream_id):
        session = get_object_or_404(DrivingSession, pk=stream_id)
        if not isinstance(request.data, dict) or "answer" not in request.data:
            return Response({"detail": "Informe answer"}, status=400)
        try:
            a, b = locate_samples(session, request.data)
            exercise = generate_exercise(request.data.get("topic", "displacement"), a, b)
        except ExerciseUnavailable as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response({
            "correct": compare_answer(exercise["expected_result"], request.data["answer"]),
            "expected_result": exercise["expected_result"],
            "solution_revealed": False,
        })
