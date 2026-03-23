from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("species", "0006_curatedobservation_created_at_and_more"),
    ]

    operations = [
        BtreeGistExtension(),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS "
                "species_curatedobservation_location_gist "
                "ON species_curatedobservation "
                "USING GIST (location);"
            ),
            reverse_sql=(
                "DROP INDEX IF EXISTS "
                "species_curatedobservation_location_gist;"
            ),
        ),
    ]
