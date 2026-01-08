# species/management/commands/deduplicate_observations.py
from django.core.management.base import BaseCommand
from species.tasks.deduplication import (
    find_duplicate_occurrence_ids,
    merge_duplicate_records,
)


class Command(BaseCommand):
    help = "Deduplicate and merge OBIS/GBIF observations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be merged without making changes",
        )
        parser.add_argument(
            "--prefer",
            type=str,
            default="OBIS",
            choices=["OBIS", "GBIF"],
            help="Which source to prefer when merging",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        prefer_source = options["prefer"]

        self.stdout.write("🔍 Scanning for duplicate occurrence_ids...")

        duplicates = find_duplicate_occurrence_ids()
        total_duplicates = duplicates.count()

        if total_duplicates == 0:
            self.stdout.write(self.style.SUCCESS("✅ No duplicates found!"))
            return

        self.stdout.write(
            f"Found {total_duplicates} occurrence_ids with duplicates"
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        merged_count = 0
        error_count = 0

        for dup in duplicates:
            occurrence_id = dup["occurrence_id"]

            try:
                result = merge_duplicate_records(
                    occurrence_id, prefer_source=prefer_source, dry_run=dry_run
                )

                if result["action"] in ["merged", "would_merge"]:
                    merged_count += 1
                    if dry_run:
                        self.stdout.write(f"  Would merge: {occurrence_id}")

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Error merging {occurrence_id}: {e}")
                )
                error_count += 1

        self.stdout.write("\n" + "=" * 50)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would merge {merged_count} records"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Merged {merged_count} records")
            )

        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"⚠️  Errors: {error_count}"))
