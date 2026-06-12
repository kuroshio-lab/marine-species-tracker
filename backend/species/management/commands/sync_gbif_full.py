# species/management/commands/sync_gbif_full.py
from datetime import datetime

from django.core.management.base import BaseCommand

from species.models import CuratedObservation
from species.tasks.gbif_api import GBIFAPIClient
from species.tasks.ingest import (
    GBIFSource,
    OffsetTraversal,
    WoRMSResolver,
    ingest_source,
)


class Command(BaseCommand):
    help = "Full GBIF historical backfill (use sparingly)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--year-start",
            type=int,
            default=2015,
            help="Start year for historical data",
        )
        parser.add_argument(
            "--year-end", type=int, help="End year (default: current year)"
        )
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Delete existing GBIF records before sync",
        )
        parser.add_argument(
            "--strategy",
            type=str,
            default="obis_network",
            choices=["obis_network", "marine_geographic"],
        )
        parser.add_argument(
            "--geometry",
            type=str,
            help="WKT polygon for marine_geographic strategy",
        )

    def handle(self, *args, **options):
        if options["clear_existing"]:
            confirm = input(
                "⚠️  Delete all existing GBIF records? Type 'yes': "
            )
            if confirm.lower() == "yes":
                deleted = CuratedObservation.objects.filter(
                    source="GBIF"
                ).delete()
                self.stdout.write(f"Deleted {deleted[0]} GBIF records")
            else:
                self.stdout.write("Aborted")
                return

        year_start = options["year_start"]
        year_end = options["year_end"] or datetime.now().year
        strategy = options["strategy"]
        geometry = options.get("geometry")

        self.stdout.write(
            f"🌊 Starting GBIF full refresh: {year_start}-{year_end}\n"
            f"   Strategy: {strategy}\n"
            "   This may take several hours..."
        )

        total_stats = {"saved": 0, "rejected": 0, "duplicates": 0}
        client = GBIFAPIClient()
        taxonomy = WoRMSResolver()

        for year in range(year_start, year_end + 1):
            self.stdout.write(f"\n📅 Processing year {year}...")

            run = ingest_source(
                GBIFSource(),
                OffsetTraversal(client, geometry_wkt=geometry, year=str(year)),
                taxonomy=taxonomy,
            )

            total_stats["saved"] += run.saved
            total_stats["rejected"] += run.rejected
            total_stats["duplicates"] += run.duplicates

            self.stdout.write(
                f"   Year {year} complete: {run.saved} records saved"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Full refresh complete!\n"
                f"   Saved: {total_stats['saved']}\n"
                f"   Rejected: {total_stats['rejected']}\n"
                f"   Duplicates: {total_stats['duplicates']}"
            )
        )
