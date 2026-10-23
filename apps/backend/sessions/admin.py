from django.contrib import admin
from .models import DrivingSession


@admin.register(DrivingSession)
class DrivingSessionAdmin(admin.ModelAdmin):
    list_display = ("stream_id", "agent_id", "car", "track", "sample_count", "last_sample_at")
    search_fields = ("agent_id", "car", "track", "stream_id")
    readonly_fields = ("stream_id", "sample_count", "first_sample_at", "last_sample_at", "created_at")
