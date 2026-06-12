# species/management/commands/sync_gbif_incremental.py
from datetime import datetime

from django.core.management.base import BaseCommand

from species.tasks.gbif_api import GBIFAPIClient
from species.tasks.ingest import (
    OCEAN_POLYGONS_WKT,
    GBIFSource,
    OceanFanout,
    OffsetTraversal,
    WoRMSResolver,
    ingest_source,
)


class Command(BaseCommand):
    help = "Fetch recent GBIF observations (incremental sync)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=str,
            default=str(datetime.now().year),
            help='Year or year range e.g. "2024" or "2023,2024"',
        )
        parser.add_argument(
            "--strategy",
            type=str,
            default="oceans",
            choices=["obis_network", "marine_geographic", "oceans"],
        )
        parser.add_argument(
            "--geometry",
            type=str,
            help="WKT polygon for marine_geographic strategy",
        )
        parser.add_argument(
            "--max-records",
            type=int,
            default=10000,
            help="Stop after this many records",
        )

    def handle(self, *args, **options):
        year = options["year"]
        strategy = options["strategy"]
        geometry = options.get("geometry")
        max_records = options["max_records"]

        client = GBIFAPIClient()
        taxonomy = WoRMSResolver()

        if strategy == "oceans":
            self.stdout.write("🌊 Running Ocean-based pipeline...")
            traversal = OceanFanout(client, OCEAN_POLYGONS_WKT, year=year)
        else:
            self.stdout.write(
                "🌊 Starting GBIF incremental sync\n"
                f"   Year: {year}\n"
                f"   Strategy: {strategy}\n"
                f"   Max records: {max_records}"
            )
            traversal = OffsetTraversal(
                client, geometry_wkt=geometry, year=year
            )

        run = ingest_source(
            GBIFSource(),
            traversal,
            taxonomy=taxonomy,
            max_records=max_records,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Incremental sync complete!\n"
                f"   Total saved: {run.saved}\n"
                f"   Total rejected: {run.rejected}\n"
                f"   Total duplicates: {run.duplicates}"
            )
        )
