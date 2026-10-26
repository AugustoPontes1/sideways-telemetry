"""Capture session identified by the AC Bridge stream_id."""
from django.db import models


class DrivingSession(models.Model):
    stream_id = models.UUIDField(primary_key=True, editable=False)
    agent_id = models.CharField(max_length=100, db_index=True)
    car = models.CharField(max_length=160)
    track = models.CharField(max_length=160)
    session_type = models.SmallIntegerField(default=0)
    first_sample_at = models.DateTimeField()
    last_sample_at = models.DateTimeField()
    sample_count = models.PositiveBigIntegerField(default=0)
    max_sequence = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_sample_at"]

    def __str__(self) -> str:
        return f"{self.car} @ {self.track} ({self.stream_id})"
