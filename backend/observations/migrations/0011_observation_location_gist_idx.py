from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("observations", "0010_alter_observation_options"),
    ]

    operations = [
        BtreeGistExtension(),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS "
                "observations_observation_location_gist "
                "ON observations_observation "
                "USING GIST (location);"
            ),
            reverse_sql=(
                "DROP INDEX IF EXISTS "
                "observations_observation_location_gist;"
            ),
        ),
    ]
