from django.urls import path
from .views import ExerciseTopicsView, SessionCheckAnswerView, SessionExerciseView

urlpatterns = [
    path("learning/topics/", ExerciseTopicsView.as_view(), name="learning-topics"),
    path("sessions/<uuid:stream_id>/exercise/", SessionExerciseView.as_view(), name="session-exercise"),
    path("sessions/<uuid:stream_id>/exercise/check/", SessionCheckAnswerView.as_view(), name="session-check"),
]
