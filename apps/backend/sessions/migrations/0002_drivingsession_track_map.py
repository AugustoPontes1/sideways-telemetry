from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("drift_sessions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="drivingsession",
            name="track_map",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
