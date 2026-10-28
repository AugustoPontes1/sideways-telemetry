from django.urls import path
from .views import (
    PublicSessionAnalysisView,
    PublicTrajectoryComparisonView,
    SessionAnalysisView,
    TrajectoryComparisonView,
)

urlpatterns = [
    path("public/sessions/<uuid:stream_id>/analysis/", PublicSessionAnalysisView.as_view(), name="public-session-analysis"),
    path("public/sessions/<uuid:stream_id>/analysis/compare/", PublicTrajectoryComparisonView.as_view(), name="public-session-compare"),
    path("sessions/<uuid:stream_id>/analysis/", SessionAnalysisView.as_view(), name="session-analysis"),
    path("sessions/<uuid:stream_id>/analysis/compare/", TrajectoryComparisonView.as_view(), name="session-compare"),
]
