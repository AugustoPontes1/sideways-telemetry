from django.urls import path
from .views import (
    ExerciseTopicsView,
    PublicExerciseTopicsView,
    PublicSessionCheckAnswerView,
    PublicSessionExerciseView,
    SessionCheckAnswerView,
    SessionExerciseView,
)

urlpatterns = [
    path("public/learning/topics/", PublicExerciseTopicsView.as_view(), name="public-learning-topics"),
    path("public/sessions/<uuid:stream_id>/exercise/", PublicSessionExerciseView.as_view(), name="public-session-exercise"),
    path("public/sessions/<uuid:stream_id>/exercise/check/", PublicSessionCheckAnswerView.as_view(), name="public-session-check"),
    path("learning/topics/", ExerciseTopicsView.as_view(), name="learning-topics"),
    path("sessions/<uuid:stream_id>/exercise/", SessionExerciseView.as_view(), name="session-exercise"),
    path("sessions/<uuid:stream_id>/exercise/check/", SessionCheckAnswerView.as_view(), name="session-check"),
]
