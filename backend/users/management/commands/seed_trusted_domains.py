from django.core.management.base import BaseCommand

from users.models import TrustedEmailDomain

TRUSTED_DOMAINS = [
    {
        "domain": "marine.csiro.au",
        "organization_name": "CSIRO Marine and Atmospheric Research",
    },
    {
        "domain": "kuroshio-lab.com",
        "organization_name": "intern admin",
    },
    {
        "domain": "mbari.org",
        "organization_name": "Monterey Bay Aquarium Research Institute",
    },
    {
        "domain": "noaa.gov",
        "organization_name": "National Oceanic and Atmospheric Administration",
    },
    {
        "domain": "edu",
        "organization_name": "US Educational Institutions",
        "notes": "Suffix match: covers all *.edu domains",
    },
    {
        "domain": "gov",
        "organization_name": "US Government Agencies",
        "notes": "Suffix match: covers all *.gov domains",
    },
]


class Command(BaseCommand):
    help = "Seed the TrustedEmailDomain table with default trusted domains"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        created_count = 0
        skipped_count = 0

        for entry in TRUSTED_DOMAINS:
            domain = entry["domain"]
            exists = TrustedEmailDomain.objects.filter(domain=domain).exists()

            if exists:
                self.stdout.write(f"  SKIP  {domain} (already exists)")
                skipped_count += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"  WOULD CREATE  {domain}"
                    f" ({entry['organization_name']})"
                )
            else:
                TrustedEmailDomain.objects.create(
                    domain=domain,
                    organization_name=entry["organization_name"],
                    auto_approve_to_community=True,
                    notes=entry.get("notes", ""),
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  CREATED  {domain}"
                        f" ({entry['organization_name']})"
                    )
                )
            created_count += 1

        action = "Would create" if dry_run else "Created"
        self.stdout.write(
            f"\n{action} {created_count}, skipped {skipped_count}"
        )
