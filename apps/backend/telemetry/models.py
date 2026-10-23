"""Amostras preservadas por sequência para evitar repetição nos reenvios."""
from django.db import models


class TelemetrySample(models.Model):
    session = models.ForeignKey(
        "drift_sessions.DrivingSession", on_delete=models.CASCADE,
        related_name="samples",
    )
    sequence = models.PositiveBigIntegerField()
    sampled_at = models.DateTimeField()
    received_at = models.DateTimeField()
    physics_packet_id = models.PositiveBigIntegerField()
    graphics_packet_id = models.PositiveBigIntegerField()
    completed_laps = models.PositiveIntegerField()
    speed_kmh = models.FloatField()
    speed_mps = models.FloatField()
    rpm = models.PositiveIntegerField()
    gear = models.SmallIntegerField()
    throttle = models.FloatField()
    brake = models.FloatField()
    clutch = models.FloatField()
    steer_angle_rad = models.FloatField()
    heading_rad = models.FloatField()
    pitch_rad = models.FloatField()
    roll_rad = models.FloatField()
    position_world_m = models.JSONField(default=list)
    velocity_world_mps = models.JSONField(default=list)
    acceleration_g = models.JSONField(default=list)
    angular_velocity_local_rad_s = models.JSONField(default=list)
    wheel_slip_raw = models.JSONField(default=list)
    # Todos os campos normalizados, para análises futuras sem migrações imediatas.
    payload = models.JSONField()
    frame_hash = models.CharField(max_length=64)

    class Meta:
        ordering = ["session_id", "sequence"]
        constraints = [
            models.UniqueConstraint(fields=["session", "sequence"], name="uq_sample_session_seq"),
        ]
        indexes = [
            models.Index(fields=["session", "sampled_at"], name="idx_session_sampledt"),
        ]

    def __str__(self) -> str:
        return f"{self.session_id} #{self.sequence}"
