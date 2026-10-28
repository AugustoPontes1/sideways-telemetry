from rest_framework import serializers
from .models import DrivingSession


class DrivingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrivingSession
        fields = [
            "stream_id", "agent_id", "car", "track", "car_visual", "session_type", "sample_count",
            "max_sequence", "first_sample_at", "last_sample_at", "created_at", "updated_at",
        ]
