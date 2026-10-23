from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ok"})
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", health),
    path("api/", include("sessions.urls")),
    path("api/", include("telemetry.urls")),
    path("api/", include("analysis.urls")),
    path("api/", include("learning.urls")),
]
