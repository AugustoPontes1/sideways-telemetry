from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("drift_sessions", "0002_drivingsession_track_map"),
    ]

    operations = [
        migrations.AddField(
            model_name="drivingsession",
            name="car_visual",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
