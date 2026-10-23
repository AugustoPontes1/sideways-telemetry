import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("sessions", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="TelemetrySample",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sequence", models.PositiveBigIntegerField()),
                ("sampled_at", models.DateTimeField()),
                ("received_at", models.DateTimeField()),
                ("physics_packet_id", models.PositiveBigIntegerField()),
                ("graphics_packet_id", models.PositiveBigIntegerField()),
                ("completed_laps", models.PositiveIntegerField()),
                ("speed_kmh", models.FloatField()),
                ("speed_mps", models.FloatField()),
                ("rpm", models.PositiveIntegerField()),
                ("gear", models.SmallIntegerField()),
                ("throttle", models.FloatField()),
                ("brake", models.FloatField()),
                ("clutch", models.FloatField()),
                ("steer_angle_rad", models.FloatField()),
                ("heading_rad", models.FloatField()),
                ("pitch_rad", models.FloatField()),
                ("roll_rad", models.FloatField()),
                ("position_world_m", models.JSONField(default=list)),
                ("velocity_world_mps", models.JSONField(default=list)),
                ("acceleration_g", models.JSONField(default=list)),
                ("angular_velocity_local_rad_s", models.JSONField(default=list)),
                ("wheel_slip_raw", models.JSONField(default=list)),
                ("payload", models.JSONField()),
                ("frame_hash", models.CharField(max_length=64)),
                ("session", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="samples", to="sessions.drivingsession",
                )),
            ],
            options={"ordering": ["session_id", "sequence"]},
        ),
        migrations.AddConstraint(
            model_name="telemetrysample",
            constraint=models.UniqueConstraint(fields=("session", "sequence"), name="uq_sample_session_seq"),
        ),
        migrations.AddIndex(
            model_name="telemetrysample",
            index=models.Index(fields=["session", "sampled_at"], name="idx_session_sampledt"),
        ),
    ]
