# species/management/commands/sync_gbif_full.py
from django.core.management.base import BaseCommand
from species.tasks.gbif_etl import fetch_and_store_gbif_data
from species.models import CuratedObservation
from datetime import datetime
import time


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

        for year in range(year_start, year_end + 1):
            self.stdout.write(f"\n📅 Processing year {year}...")

            offset = 0
            year_saved = 0

            while True:
                stats = fetch_and_store_gbif_data(
                    geometry_wkt=geometry,
                    year=str(year),
                    limit=300,
                    offset=offset,
                    strategy=strategy,
                )

                year_saved += stats["saved"]
                total_stats["saved"] += stats["saved"]
                total_stats["rejected"] += stats["rejected"]
                total_stats["duplicates"] += stats["duplicates"]

                self.stdout.write(
                    f"   Offset {offset}: +{stats['saved']} saved, "
                    f"{stats['rejected']} rejected"
                )

                if stats["processed"] < 300:
                    break

                offset += 300
                time.sleep(0.5)

            self.stdout.write(
                f"   Year {year} complete: {year_saved} records saved"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Full refresh complete!\n"
                f"   Saved: {total_stats['saved']}\n"
                f"   Rejected: {total_stats['rejected']}\n"
                f"   Duplicates: {total_stats['duplicates']}"
            )
        )
