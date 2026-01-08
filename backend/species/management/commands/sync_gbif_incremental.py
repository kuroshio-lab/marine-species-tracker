# species/management/commands/sync_gbif_incremental.py
from django.core.management.base import BaseCommand
from species.tasks.gbif_etl import fetch_and_store_gbif_data
from datetime import datetime
import time


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
            default="obis_network",
            choices=["obis_network", "marine_geographic"],
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

        self.stdout.write(
            "🌊 Starting GBIF incremental sync\n"
            f"   Year: {year}\n"
            f"   Strategy: {strategy}\n"
            f"   Max records: {max_records}"
        )

        offset = 0
        limit = 300
        total_saved = 0
        total_rejected = 0
        total_duplicates = 0

        while total_saved < max_records:
            self.stdout.write(f"\n📡 Fetching offset {offset}...")

            stats = fetch_and_store_gbif_data(
                geometry_wkt=geometry,
                year=year,
                limit=limit,
                offset=offset,
                strategy=strategy,
            )

            total_saved += stats["saved"]
            total_rejected += stats["rejected"]
            total_duplicates += stats["duplicates"]

            self.stdout.write(
                f"   +{stats['saved']} saved, "
                f"{stats['rejected']} rejected, "
                f"{stats['duplicates']} duplicates"
            )

            # Stop conditions
            if stats["processed"] < limit:
                self.stdout.write("   No more records available")
                break

            if stats["saved"] == 0 and stats["duplicates"] > limit * 0.8:
                self.stdout.write("   Mostly duplicates, stopping")
                break

            offset += limit
            time.sleep(0.5)  # Be nice to GBIF

        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Incremental sync complete!\n"
                f"   Total saved: {total_saved}\n"
                f"   Total rejected: {total_rejected}\n"
                f"   Total duplicates: {total_duplicates}"
            )
        )
