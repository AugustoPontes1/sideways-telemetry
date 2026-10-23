from django.urls import path
from .views import SessionAnalysisView, TrajectoryComparisonView

urlpatterns = [
    path("sessions/<uuid:stream_id>/analysis/", SessionAnalysisView.as_view(), name="session-analysis"),
    path("sessions/<uuid:stream_id>/analysis/compare/", TrajectoryComparisonView.as_view(), name="session-compare"),
]
