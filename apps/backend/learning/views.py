"""Study Mode API: the solution appears only when reveal=1."""
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from sessions.models import DrivingSession
from telemetry.models import TelemetrySample
from .services import TOPICS, ExerciseUnavailable, compare_answer, generate_exercise


def locate_samples(session, query):
    """Use the two most recent samples when indices are not provided."""
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


def locate_three_samples(session, query):
    first, second = locate_samples(session, query)
    third_raw = query.get("c")
    try:
        third_seq = int(third_raw)
    except (ValueError, TypeError) as exc:
        raise ExerciseUnavailable("c precisa ser uma sequência inteira") from exc
    if third_seq < 0 or third_seq in {first.sequence, second.sequence}:
        raise ExerciseUnavailable("a, b e c precisam ser sequências distintas não negativas")
    third = TelemetrySample.objects.filter(session=session, sequence=third_seq).first()
    if not third:
        raise ExerciseUnavailable("A amostra c não existe nesta sessão")
    return first, second, third


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
            if topic.startswith("lesson19_"):
                exercise = generate_exercise(topic, None, None, reveal=reveal)
            elif topic == "basis_dimension_3d":
                a, b, c = locate_three_samples(session, request.query_params)
                exercise = generate_exercise(topic, a, b, c, reveal=reveal)
            else:
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
            topic = request.data.get("topic", "displacement")
            if topic.startswith("lesson19_"):
                exercise = generate_exercise(topic, None, None)
            elif topic == "basis_dimension_3d":
                a, b, c = locate_three_samples(session, request.data)
                exercise = generate_exercise(topic, a, b, c)
            else:
                a, b = locate_samples(session, request.data)
                exercise = generate_exercise(topic, a, b)
        except ExerciseUnavailable as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response({
            "correct": compare_answer(exercise["expected_result"], request.data["answer"]),
            "expected_result": exercise["expected_result"],
            "solution_revealed": False,
        })


class PublicExerciseTopicsView(ExerciseTopicsView):
    permission_classes = [AllowAny]


class PublicSessionExerciseView(SessionExerciseView):
    permission_classes = [AllowAny]


class PublicSessionCheckAnswerView(SessionCheckAnswerView):
    permission_classes = [AllowAny]
