from rest_framework import serializers
from .models import TelemetrySample


class TelemetrySampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemetrySample
        fields = [
            "sequence", "sampled_at", "received_at", "speed_kmh", "speed_mps",
            "rpm", "gear", "throttle", "brake", "clutch", "steer_angle_rad",
            "heading_rad", "pitch_rad", "roll_rad", "position_world_m",
            "velocity_world_mps", "completed_laps",
        ]
