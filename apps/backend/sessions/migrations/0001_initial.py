from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="DrivingSession",
            fields=[
                ("stream_id", models.UUIDField(primary_key=True, serialize=False, editable=False)),
                ("agent_id", models.CharField(max_length=100, db_index=True)),
                ("car", models.CharField(max_length=160)),
                ("track", models.CharField(max_length=160)),
                ("session_type", models.SmallIntegerField(default=0)),
                ("first_sample_at", models.DateTimeField()),
                ("last_sample_at", models.DateTimeField()),
                ("sample_count", models.PositiveBigIntegerField(default=0)),
                ("max_sequence", models.PositiveBigIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-last_sample_at"]},
        ),
    ]
