from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone

from .models import User, TrustedEmailDomain


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Enhanced User admin with researcher verification workflow.
    """

    list_display = [
        "username",
        "email",
        "role_badge",
        "email_verified_badge",
        "profile_complete_badge",
        "verification_status",
        "date_joined",
    ]

    list_filter = [
        "role",
        "email_verified",
        "is_staff",
        "is_active",
        "date_joined",
    ]

    search_fields = [
        "username",
        "email",
        "institution_name",
        "orcid",
    ]

    fieldsets = (
        ("Basic Info", {"fields": ("username", "email", "password")}),
        (
            "Role & Verification",
            {
                "fields": (
                    "role",
                    "email_verified",
                    "verification_requested_at",
                    "verification_completed_at",
                    "verified_by",
                    "verification_notes",
                )
            },
        ),
        (
            "Researcher Details",
            {
                "fields": (
                    "institution_name",
                    "ror_id",
                    "orcid",
                    "research_focus",
                    "years_experience",
                    "bio",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Important dates",
            {
                "fields": ("last_login", "date_joined"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = [
        "approve_to_community",
        "approve_to_institutional",
        "reject_verification",
        "send_verification_reminder",
    ]

    def role_badge(self, obj):
        """Display role with color-coded badge."""
        colors = {
            User.HOBBYIST: "#A7B2B7",  # gray-500
            User.RESEARCHER_PENDING: "#FFCF5C",  # warning-500
            User.RESEARCHER_COMMUNITY: "#30C39E",  # success-500
            User.RESEARCHER_INSTITUTIONAL: "#0077BA",  # primary-500
        }
        color = colors.get(obj.role, "#A7B2B7")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px'
            " 8px; border-radius: 4px; font-size: 11px; font-weight:"
            ' bold;">{}</span>',
            color,
            obj.get_role_display(),
        )

    role_badge.short_description = "Role"

    def email_verified_badge(self, obj):
        """Display email verification status."""
        if obj.email_verified:
            return format_html('<span style="color: #30C39E;">✓</span>')
        return format_html('<span style="color: #D64550;">✗</span>')

    email_verified_badge.short_description = "Email"

    def profile_complete_badge(self, obj):
        """Display profile completion status for researchers."""
        if obj.role == User.HOBBYIST:
            return "-"

        if obj.role == User.RESEARCHER_PENDING:
            if obj.needs_researcher_profile_completion:
                return format_html(
                    '<span style="color: #FF6F59;">⚠ Incomplete</span>'
                )
            return format_html(
                '<span style="color: #30C39E;">✓ Complete</span>'
            )

        return format_html('<span style="color: #30C39E;">✓</span>')

    profile_complete_badge.short_description = "Profile"

    def verification_status(self, obj):
        """Display verification workflow status."""
        if obj.role == User.HOBBYIST:
            return "-"

        if obj.role == User.RESEARCHER_PENDING:
            if not obj.verification_requested_at:
                return format_html(
                    '<span style="color: #FF6F59;">⚠ Not Requested</span>'
                )
            days_pending = (
                timezone.now() - obj.verification_requested_at
            ).days
            color = "#FFCF5C" if days_pending < 7 else "#FF6F59"
            return format_html(
                '<span style="color: {};">⏱ {} days pending</span>',
                color,
                days_pending,
            )

        if obj.verification_completed_at:
            return format_html(
                '<span style="color: #30C39E;">✓ Verified {}</span>',
                obj.verification_completed_at.strftime("%Y-%m-%d"),
            )

        return "-"

    verification_status.short_description = "Status"

    @admin.action(description="✓ Approve to Community Verified")
    def approve_to_community(self, request, queryset):
        """Approve pending researchers to Community tier."""
        updated = 0
        for user in queryset.filter(role=User.RESEARCHER_PENDING):
            user.role = User.RESEARCHER_COMMUNITY
            user.verification_completed_at = timezone.now()
            user.verified_by = request.user
            user.save()
            updated += 1
            # TODO: Send approval email notification

        self.message_user(
            request,
            f"Successfully approved {updated} researcher(s) to Community"
            " Verified.",
        )

    @admin.action(description="✓✓ Approve to Institutional Verified")
    def approve_to_institutional(self, request, queryset):
        """Approve researchers to Institutional tier."""
        updated = 0
        for user in queryset.filter(
            role__in=[User.RESEARCHER_PENDING, User.RESEARCHER_COMMUNITY]
        ):
            user.role = User.RESEARCHER_INSTITUTIONAL
            user.verification_completed_at = timezone.now()
            user.verified_by = request.user
            user.save()
            updated += 1
            # TODO: Send approval email notification

        self.message_user(
            request,
            f"Successfully approved {updated} researcher(s) to Institutional"
            " Verified.",
        )

    @admin.action(description="✗ Reject Verification")
    def reject_verification(self, request, queryset):
        """Reject pending researchers (revert to Hobbyist)."""
        updated = 0
        for user in queryset.filter(role=User.RESEARCHER_PENDING):
            user.role = User.HOBBYIST
            user.verification_requested_at = None
            user.save()
            updated += 1
            # TODO: Send rejection email notification

        self.message_user(
            request,
            f"Rejected {updated} researcher verification(s).",
            level="warning",
        )

    @admin.action(description="📧 Send Verification Reminder")
    def send_verification_reminder(self, request, queryset):
        """Send reminder email to pending researchers."""
        # TODO: Implement email reminder
        self.message_user(
            request,
            f"Sent verification reminder to {queryset.count()} user(s).",
        )


@admin.register(TrustedEmailDomain)
class TrustedEmailDomainAdmin(admin.ModelAdmin):
    """
    Admin interface for managing trusted institutional domains.
    """

    list_display = [
        "domain",
        "organization_name",
        "ror_id",
        "auto_approve_badge",
        "created_at",
    ]

    list_filter = [
        "auto_approve_to_community",
        "created_at",
    ]

    search_fields = [
        "domain",
        "organization_name",
        "ror_id",
    ]

    fieldsets = (
        (None, {"fields": ("domain", "organization_name", "ror_id")}),
        ("Settings", {"fields": ("auto_approve_to_community", "notes")}),
    )

    def auto_approve_badge(self, obj):
        """Display auto-approval status."""
        if obj.auto_approve_to_community:
            return format_html(
                '<span style="color: #30C39E;">✓ Auto-approve</span>'
            )
        return format_html(
            '<span style="color: #A7B2B7;">Manual review</span>'
        )

    auto_approve_badge.short_description = "Auto Approval"
