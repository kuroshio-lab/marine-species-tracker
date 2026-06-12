# species/management/commands/sync_gbif_by_oceans.py
import time

from django.core.management.base import BaseCommand

from species.models import CuratedObservation
from species.tasks.gbif_api import GBIFAPIClient
from species.tasks.ingest import (
    OCEAN_POLYGONS_WKT,
    GBIFSource,
    OceanFanout,
    WoRMSResolver,
    ingest_source,
)


class Command(BaseCommand):
    help = "Sync GBIF data using ocean polygon strategy"

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=str,
            help='Year or year range (e.g., "2024" or "2023,2024")',
            required=True,
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=300,
            help="Records per request per ocean (default: 300)",
        )
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Delete all existing GBIF records before sync (FULL MODE)",
        )

    def handle(self, *args, **options):
        year = options["year"]
        limit = options["limit"]
        clear_existing = options["clear_existing"]

        # FULL MODE: Clear existing GBIF data
        if clear_existing:
            confirm = input(
                "⚠️  FULL REFRESH MODE: This will DELETE all existing GBIF"
                " records.\n   Type 'yes' to confirm: "
            )
            if confirm.lower() == "yes":
                deleted_count = CuratedObservation.objects.filter(
                    source="GBIF"
                ).delete()[0]
                self.stdout.write(
                    self.style.WARNING(
                        f"🗑️  Deleted {deleted_count} existing GBIF records"
                    )
                )
            else:
                self.stdout.write(self.style.ERROR("❌ Aborted"))
                return

        self.stdout.write(
            "🌊 Starting GBIF Ocean-based Sync\n"
            f"   Year: {year}\n"
            f"   Limit per ocean: {limit}\n"
            f"   Mode: {'FULL REFRESH' if clear_existing else 'INCREMENTAL'}"
        )
        self.stdout.write("=" * 50)

        start_time = time.time()

        run = ingest_source(
            GBIFSource(),
            OceanFanout(GBIFAPIClient(), OCEAN_POLYGONS_WKT, year=year),
            taxonomy=WoRMSResolver(),
            page_size=limit,
        )

        elapsed_time = time.time() - start_time

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(
            self.style.SUCCESS(
                "✅ GBIF Ocean Sync Complete!\n"
                f"   Total Processed: {run.processed:,}\n"
                f"   Total Saved: {run.saved:,}\n"
                f"   Time Elapsed: {elapsed_time:.1f}s"
            )
        )
