from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import TimeStampedModel


class User(TimeStampedModel, AbstractUser):
    """
    Extended User model with researcher verification support.
    """

    # Role choices with verification tiers
    HOBBYIST = "hobbyist"
    RESEARCHER_PENDING = "researcher_pending"
    RESEARCHER_COMMUNITY = "researcher_community"
    RESEARCHER_INSTITUTIONAL = "researcher_institutional"

    ROLE_CHOICES = [
        (HOBBYIST, "Hobbyist"),
        (RESEARCHER_PENDING, "Researcher - Pending Verification"),
        (RESEARCHER_COMMUNITY, "Researcher - Community Verified"),
        (RESEARCHER_INSTITUTIONAL, "Researcher - Institutionally Verified"),
    ]

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default=HOBBYIST,
        blank=False,
        null=False,
    )

    # Email verification (existing)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(
        max_length=100, blank=True, null=True
    )
    email_verification_token_created = models.DateTimeField(
        blank=True, null=True
    )

    institution_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of research institution or organization",
    )
    ror_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Research Organization Registry ID",
    )

    orcid = models.CharField(
        max_length=19,
        blank=True,
        null=True,
        help_text="ORCID identifier (format: 0000-0000-0000-0000)",
    )

    research_focus = models.JSONField(
        default=list, blank=True, help_text="Array of research focus areas"
    )

    years_experience = models.IntegerField(
        null=True, blank=True, help_text="Years of research experience"
    )

    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="Brief professional bio (optional)",
    )

    # Verification tracking
    verification_requested_at = models.DateTimeField(null=True, blank=True)
    verification_completed_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="researchers_verified",
    )
    verification_notes = models.TextField(
        blank=True, help_text="Admin notes about verification process"
    )

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["orcid"]),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_verified_researcher(self):
        """Check if user is a verified researcher (Community or Institutional)."""
        return self.role in [
            self.RESEARCHER_COMMUNITY,
            self.RESEARCHER_INSTITUTIONAL,
        ]

    @property
    def can_validate_observations(self):
        """Check if user has permission to validate observations."""
        return self.is_staff or self.is_verified_researcher

    @property
    def needs_researcher_profile_completion(self):
        """Check if researcher needs to complete their profile."""
        if self.role != self.RESEARCHER_PENDING:
            return False
        # Check if required researcher fields are filled
        return not (self.institution_name and self.research_focus)


class TrustedEmailDomain(TimeStampedModel):
    """
    Whitelist of trusted institutional email domains for auto-verification.
    """

    domain = models.CharField(
        max_length=255,
        unique=True,
        help_text="Email domain (e.g., marine.university.edu)",
    )
    organization_name = models.CharField(max_length=255)
    ror_id = models.CharField(max_length=50, blank=True, null=True)
    auto_approve_to_community = models.BooleanField(
        default=True, help_text="Automatically verify users to Community tier"
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Trusted Email Domain"
        verbose_name_plural = "Trusted Email Domains"
        ordering = ["organization_name"]

    def __str__(self):
        return f"{self.domain} ({self.organization_name})"

    @classmethod
    def find_matching_domain(cls, email_domain):
        """
        Find a TrustedEmailDomain matching the given email domain.
        Supports both exact matches (e.g., 'mbari.org') and suffix matches
        (e.g., 'edu' matches 'stanford.edu', 'mit.edu').
        Returns the most specific (longest) match, or None.
        """
        from django.db.models import F, Value
        from django.db.models.functions import Length

        # Try exact match first
        try:
            return cls.objects.get(domain=email_domain)
        except cls.DoesNotExist:
            pass

        # Try suffix match: find all trusted domains where the email domain
        # ends with '.{trusted_domain}' (e.g., 'stanford.edu' ends with '.edu')
        candidates = []
        for td in cls.objects.all():
            if email_domain.endswith(f".{td.domain}"):
                candidates.append(td)

        if not candidates:
            return None

        # Return the most specific (longest domain) match
        return max(candidates, key=lambda td: len(td.domain))
