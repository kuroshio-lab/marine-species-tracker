import base64
import secrets
import logging
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from observations.serializers import ObservationGeoSerializer
from core.logging_utils import set_current_user, clear_current_user

User = get_user_model()
logger = logging.getLogger("users")


class RegisterSerializer(serializers.ModelSerializer):
    """
    Simplified registration - only email, username, password, and role.
    Researcher profile completion happens after email verification.
    """

    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "password", "username", "role")

    def validate_email(self, value):
        """Validate email and check against trusted domains for researchers."""
        email = value.lower()

        # Check if user with this email already exists
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return email

    def create(self, validated_data):
        email = validated_data["email"]
        role = validated_data.get("role", User.HOBBYIST)

        set_current_user(email)
        logger.info(f"Attempting to register new user: {email} as {role}")

        try:
            # Create inactive user
            user = User.objects.create_user(
                email=email,
                username=validated_data["username"],
                password=validated_data["password"],
                role=role,
                is_active=False,  # User is inactive until email is verified
            )

            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            user.email_verification_token = verification_token
            user.email_verification_token_created = timezone.now()

            # If researcher, set verification request timestamp
            if role == User.RESEARCHER_PENDING:
                user.verification_requested_at = timezone.now()

                # Check if email domain is trusted for auto-approval
                from .models import TrustedEmailDomain

                domain = email.split("@")[-1].lower()

                try:
                    trusted_domain = TrustedEmailDomain.objects.get(
                        domain=domain
                    )
                    if trusted_domain.auto_approve_to_community:
                        user.verification_notes = (
                            f"Email domain {domain} is whitelisted. Will"
                            " auto-approve to Community tier after profile"
                            " completion."
                        )
                        logger.info(
                            f"User {email} registered with trusted domain"
                            f" {domain}"
                        )
                except TrustedEmailDomain.DoesNotExist:
                    logger.info(
                        f"User {email} registered with non-whitelisted domain"
                        f" {domain}"
                    )

            user.save()

            # Send verification email
            self._send_verification_email(user, verification_token)
            logger.info(
                "User registered successfully. Verification email sent to:"
                f" {email}"
            )

            return user
        except Exception as e:
            logger.error(f"Failed to register user {email}: {str(e)}")
            raise
        finally:
            clear_current_user()

    def _send_verification_email(self, user, token):
        """Send email verification link to user"""
        if settings.DEBUG:
            current_site_domain = "localhost:3000"
            protocol = "http"
        else:
            current_site_domain = "species.kuroshio-lab.com"
            protocol = "https"

        verification_url = (
            f"{protocol}://{current_site_domain}/verify-email?token={token}"
        )

        email_context = {
            "user": user,
            "verification_url": verification_url,
            "protocol": protocol,
            "domain": current_site_domain,
            "is_researcher": user.role == User.RESEARCHER_PENDING,
        }

        # Use different template for researchers
        if user.role == User.RESEARCHER_PENDING:
            email_html_template = "users/email_verification_researcher.html"
            email_plain_template = "users/email_verification_researcher.txt"
        else:
            email_html_template = "users/email_verification_email.html"
            email_plain_template = "users/email_verification_email.txt"

        email_html_message = render_to_string(
            email_html_template, email_context
        )
        email_plain_message = render_to_string(
            email_plain_template, email_context
        )

        try:
            send_mail(
                subject="Verify Your Email Address",
                message=email_plain_message,
                html_message=email_html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.debug(
                f"Verification email successfully queued for {user.email}"
            )
        except Exception as e:
            logger.error(
                f"Error sending verification email to {user.email}: {str(e)}"
            )
            raise


class ResearcherProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for completing researcher profile after email verification.
    """

    class Meta:
        model = User
        fields = [
            "institution_name",
            "ror_id",
            "orcid",
            "research_focus",
            "years_experience",
            "bio",
        ]

    def validate(self, data):
        """Validate required researcher fields."""
        if not data.get("institution_name"):
            raise serializers.ValidationError(
                {"institution_name": "Institution name is required."}
            )

        if not data.get("research_focus") or len(data["research_focus"]) == 0:
            raise serializers.ValidationError(
                {
                    "research_focus": (
                        "Please select at least one research focus area."
                    )
                }
            )

        # Validate ORCID format if provided
        orcid = data.get("orcid")
        if orcid:
            import re

            if not re.match(r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$", orcid):
                raise serializers.ValidationError(
                    {
                        "orcid": (
                            "Invalid ORCID format. Expected:"
                            " 0000-0000-0000-0000"
                        )
                    }
                )

        return data

    def update(self, instance, validated_data):
        """Update researcher profile and check for auto-approval."""
        for field, value in validated_data.items():
            setattr(instance, field, value)

        # Check if email domain is trusted for auto-approval
        from .models import TrustedEmailDomain

        email_domain = instance.email.split("@")[-1].lower()

        try:
            trusted_domain = TrustedEmailDomain.objects.get(
                domain=email_domain
            )
            if trusted_domain.auto_approve_to_community:
                instance.role = User.RESEARCHER_COMMUNITY
                instance.verification_completed_at = timezone.now()
                instance.verification_notes = (
                    "Auto-approved to Community tier based on trusted domain:"
                    f" {email_domain}"
                )
                logger.info(
                    f"User {instance.email} auto-approved to Community tier"
                )
        except TrustedEmailDomain.DoesNotExist:
            # Remains pending, needs admin review
            logger.info(
                f"User {instance.email} profile completed, awaiting admin"
                " review"
            )

        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "role",
            "email_verified",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "role",
            "email_verified",
            "created_at",
            "updated_at",
        )


class UserProfileSerializer(UserSerializer):
    observation_count = serializers.SerializerMethodField()
    observations = ObservationGeoSerializer(many=True, read_only=True)
    needs_researcher_profile_completion = serializers.BooleanField(
        read_only=True
    )
    verification_status_display = serializers.SerializerMethodField()
    can_validate_observations = serializers.BooleanField(read_only=True)
    is_verified_researcher = serializers.BooleanField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            "observation_count",
            "observations",
            "needs_researcher_profile_completion",
            "verification_status_display",
            "can_validate_observations",
            "is_verified_researcher",
            # Researcher fields
            "institution_name",
            "ror_id",
            "orcid",
            "research_focus",
            "years_experience",
            "bio",
        )

    def get_observation_count(self, obj):
        return obj.observations.count()

    def get_verification_status_display(self, obj):
        status_map = {
            User.HOBBYIST: "Not Applicable",
            User.RESEARCHER_PENDING: "Pending Verification",
            User.RESEARCHER_COMMUNITY: "Community Verified",
            User.RESEARCHER_INSTITUTIONAL: "Institutionally Verified",
        }
        return status_map.get(obj.role, "Unknown")


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username = None
    email = serializers.EmailField()
    password = serializers.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        set_current_user(email)

        if not email or not password:
            logger.warning("Login attempt missing credentials.")
            raise serializers.ValidationError(
                "Must include 'email' and 'password'."
            )

        logger.info(f"Login attempt received for: {email}")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"Login failed: No user found with email {email}")
            raise serializers.ValidationError("No user with this email.")

        # Check if user is active (email verified)
        if not user.is_active:
            logger.warning(
                f"Login failed: User {email} is inactive (unverified email)."
            )
            raise serializers.ValidationError(
                "Please verify your email address before signing in."
            )

        attrs["username"] = user.username  # SimpleJWT expects 'username'

        try:
            data = super().validate(attrs)
            logger.info(f"Login successful for user: {email}")
            return data
        except Exception as e:
            logger.error(f"Login authentication failed for {email}: {str(e)}")
            raise
        finally:
            clear_current_user()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "No user is associated with this email address."
            )
        self.user = user
        return value

    def save(self):
        user = self.user
        token = default_token_generator.make_token(user)
        uid = base64.urlsafe_b64encode(force_bytes(user.pk)).decode("ascii")

        if settings.DEBUG:
            current_site_domain = "localhost:3000"
            protocol = "http"
        else:
            current_site_domain = "species.kuroshio-lab.com"
            protocol = "https"

        reset_link = (
            f"{protocol}://{current_site_domain}/reset-password/{uid}/{token}/"
        )

        email_context = {
            "user": user,
            "reset_link": reset_link,
            "protocol": protocol,
            "domain": current_site_domain,
            "uid": uid,
            "token": token,
        }
        email_html_message = render_to_string(
            "users/password_reset_email.html", email_context
        )
        email_plain_message = render_to_string(
            "users/password_reset_email.txt", email_context
        )

        send_mail(
            subject="Password Reset Request",
            message=email_plain_message,
            html_message=email_html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )


class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        write_only=True, required=True, min_length=8
    )
    re_new_password = serializers.CharField(
        write_only=True, required=True, min_length=8
    )

    def validate(self, data):
        if data["new_password"] != data["re_new_password"]:
            raise serializers.ValidationError(
                {"new_password": "New passwords must match."}
            )
        return data

    def save(self):
        try:
            uid = urlsafe_base64_decode(self.validated_data["uidb64"]).decode(
                "ascii"
            )
            user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError):
            print(f"Invalid uidb64: {self.validated_data.get('uidb64')}")
            raise serializers.ValidationError(
                {"uidb64": "Invalid user ID in reset link."}
            )
        except User.DoesNotExist:
            print(f"User not found for uid: {uid}")
            raise serializers.ValidationError({"uidb64": "User not found."})

        token_valid = default_token_generator.check_token(
            user, self.validated_data["token"]
        )

        if user is not None and token_valid:
            user.set_password(self.validated_data["new_password"])
            user.save()
            return user
        else:
            print(
                f"Token validation failed. User: {user}, Token:"
                f" {self.validated_data.get('token')[:10]}..., Valid:"
                f" {token_valid}"
            )
            raise serializers.ValidationError(
                {"token": "The reset link is invalid or has expired."}
            )


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)

    def validate_token(self, value):
        try:
            user = User.objects.get(
                email_verification_token=value,
                is_active=False,
                email_verified=False,
            )

            # Check if token is expired (24 hours)
            if user.email_verification_token_created:
                token_age = (
                    timezone.now() - user.email_verification_token_created
                )
                if token_age.total_seconds() > 24 * 60 * 60:  # 24 hours
                    raise serializers.ValidationError(
                        "Verification token has expired."
                    )

            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token.")

    def save(self):
        token = self.validated_data["token"]
        user = User.objects.get(email_verification_token=token)
        user.is_active = True
        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_token_created = None
        user.save()
        return user
