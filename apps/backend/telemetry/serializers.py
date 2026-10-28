from rest_framework import serializers
from .models import TelemetrySample


class TelemetrySampleSerializer(serializers.ModelSerializer):
    car_damage = serializers.SerializerMethodField()

    def get_car_damage(self, obj):
        value = obj.payload.get("car_damage", [0.0] * 5)
        return value if isinstance(value, list) and len(value) == 5 else [0.0] * 5

    class Meta:
        model = TelemetrySample
        fields = [
            "sequence", "sampled_at", "received_at", "speed_kmh", "speed_mps",
            "rpm", "gear", "throttle", "brake", "clutch", "steer_angle_rad",
            "heading_rad", "pitch_rad", "roll_rad", "position_world_m",
            "velocity_world_mps", "completed_laps",
            "car_damage",
        ]
