from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from users.models import User


class Command(BaseCommand):
    help = "Approve a pending researcher by username or email"

    def add_arguments(self, parser):
        parser.add_argument(
            "user", help="Username or email of the researcher to approve"
        )
        parser.add_argument(
            "--tier",
            choices=["community", "institutional"],
            default="community",
            help="Verification tier to grant (default: community)",
        )
        parser.add_argument(
            "--notes",
            type=str,
            default="",
            help="Optional verification notes",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without actually updating",
        )

    def handle(self, *args, **options):
        identifier = options["user"]

        try:
            user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                raise CommandError(
                    f'No user found with username or email "{identifier}"'
                )

        if user.role not in (
            User.RESEARCHER_PENDING,
            User.RESEARCHER_COMMUNITY,
            User.RESEARCHER_INSTITUTIONAL,
        ):
            self.stdout.write(
                self.style.WARNING(
                    f"User {user.username} has role '{user.role}', not a"
                    " researcher. Proceeding anyway."
                )
            )

        new_role = (
            User.RESEARCHER_INSTITUTIONAL
            if options["tier"] == "institutional"
            else User.RESEARCHER_COMMUNITY
        )

        self.stdout.write(f"User:     {user.username} ({user.email})")
        self.stdout.write(f"Current:  {user.role}")
        self.stdout.write(f"New role: {new_role}")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes made."))
            return

        user.role = new_role
        user.verification_completed_at = timezone.now()
        if options["notes"]:
            user.verification_notes = options["notes"]
        user.save(
            update_fields=[
                "role",
                "verification_completed_at",
                "verification_notes",
            ]
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully approved {user.username} as {new_role}."
            )
        )
