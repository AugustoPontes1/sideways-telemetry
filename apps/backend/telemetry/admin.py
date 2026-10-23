from django.contrib import admin
from .models import TelemetrySample


@admin.register(TelemetrySample)
class TelemetrySampleAdmin(admin.ModelAdmin):
    list_display = ("id", "session_id", "sequence", "sampled_at", "speed_kmh", "rpm")
    list_filter = ("session__track",)
    search_fields = ("session__stream_id",)
    readonly_fields = ("payload", "frame_hash")
