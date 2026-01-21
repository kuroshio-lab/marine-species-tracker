import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserAuth:

    register_url = "/api/v1/auth/register/"
    login_url = "/api/v1/auth/login/"
    user_url = "/api/v1/auth/user/"
    refresh_url = "/api/v1/auth/refresh/"
    profile_me_url = "/api/v1/auth/profiles/me/"
    password_reset_request_url = "/api/v1/auth/password-reset/"
    password_reset_confirm_url = "/api/v1/auth/password-reset/confirm/"
    complete_researcher_profile_url = (
        "/api/v1/auth/researcher/complete-profile/"
    )

    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def register_user(self, client):
        payload = {
            "email": "user@example.com",
            "username": "diverbob",
            "password": "testpassword123",
            "role": "hobbyist",
        }
        response = client.post(self.register_url, payload, format="json")
        assert response.status_code == 200 or response.status_code == 201
        return response.data

    def test_register(self, client):
        # Registration should return id, email, username
        resp = client.post(
            self.register_url,
            {
                "email": "user@example.com",
                "username": "diverbob",
                "password": "testpassword123",
                "role": "hobbyist",
            },
            format="json",
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert "id" in data
        assert data["email"] == "user@example.com"
        assert data["username"] == "diverbob"
        assert data["role"] == "hobbyist"

    def test_login_missing_field(self, client, register_user):
        # Login missing username: should return error
        user_obj = User.objects.get(email=register_user["email"])
        user_obj.is_active = True
        user_obj.email_verified = True
        user_obj.save()
        # Test case 1: Login missing email - should return error for 'email' field
        resp_missing_email = client.post(
            self.login_url,
            {
                "password": "testpassword123",
                # "email" is intentionally missing
            },
            format="json",
        )
        assert resp_missing_email.status_code == 400
        assert "email" in resp_missing_email.data
        assert "This field is required." in resp_missing_email.data["email"]

        # Test case 2: Login missing password - should return error for 'password' field
        resp_missing_password = client.post(
            self.login_url,
            {
                "email": "user@example.com",
                # "password" is intentionally missing
            },
            format="json",
        )
        assert resp_missing_password.status_code == 400
        assert "password" in resp_missing_password.data
        assert (
            "This field is required." in resp_missing_password.data["password"]
        )

    def test_login_invalid_username(self, client, register_user):
        # Activate the user first
        user_obj = User.objects.get(email=register_user["email"])
        user_obj.is_active = True
        user_obj.email_verified = True
        user_obj.save()
        resp = client.post(
            self.login_url,
            {
                "username": "lol",
                "email": "user@example.com",
                "password": "wrongpassword",
                "role": "hobbyist",
            },
            format="json",
        )
        assert resp.status_code == 401 or resp.status_code == 400
        assert "detail" in resp.data

    def test_login_success(self, client, register_user):
        # Right username, email, password: should return refresh & access
        user_obj = User.objects.get(email=register_user["email"])
        user_obj.is_active = True
        user_obj.email_verified = True
        user_obj.save()

        resp = client.post(
            self.login_url,
            {
                "username": "diverbob",
                "email": "user@example.com",
                "password": "testpassword123",
                "role": "hobbyist",
            },
            format="json",
        )
        assert resp.status_code == 200
        assert "refresh" in resp.data and "access" in resp.data
        self.tokens = resp.data

    def test_patch_user(self, client, register_user):
        # Update user username with PATCH and Bearer token
        user_obj = User.objects.get(email=register_user["email"])
        user_obj.is_active = True
        user_obj.email_verified = True
        user_obj.save()

        resp = client.post(
            self.login_url,
            {
                "username": "diverbob",
                "email": "user@example.com",
                "password": "testpassword123",
                "role": "hobbyist",
            },
            format="json",
        )
        token = resp.data["access"]
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        patch_resp = client.patch(
            self.user_url, {"username": "diveralice"}, format="json"
        )
        assert patch_resp.status_code == 200
        data = patch_resp.data
        assert data["username"] == "diveralice"

    def test_register_invalid_role(self, client):
        resp = client.post(
            self.register_url,
            {
                "email": "baduser@example.com",
                "username": "invalidrole",
                "password": "testpassword123",
                "role": "pirate",
            },
            format="json",
        )
        assert resp.status_code == 400
        assert "role" in resp.data or "role" in resp.json()

    def test_refresh_token(self, client, register_user):
        # Login first
        user_obj = User.objects.get(email=register_user["email"])
        user_obj.is_active = True
        user_obj.email_verified = True
        user_obj.save()

        resp = client.post(
            self.login_url,
            {
                "username": "diverbob",
                "email": "user@example.com",
                "password": "testpassword123",
                "role": "hobbyist",
            },
            format="json",
        )
        refresh = resp.data["refresh"]

        refresh_resp = client.post(
            self.refresh_url, {"refresh": refresh}, format="json"
        )
        assert refresh_resp.status_code == 200
        # Access token must be present
        assert "access" in refresh_resp.data

        # Second refresh (simulate refresh chain)
        refresh_resp2 = client.post(
            self.refresh_url, {"refresh": refresh}, format="json"
        )
        assert refresh_resp2.status_code == 200
        assert "access" in refresh_resp2.data

    def create_observation_for_user(
        self, client, token, payload_override=None
    ):
        """
        Helper to create an observation for the current authenticated user.
        You may need to adjust this based on your /observations/ endpoint structure.
        """
        obs_url = "/api/v1/observations/"
        payload = {
            "speciesName": "Test Fish",
            "observationDatetime": "2024-10-29T12:00:00Z",
            "location": "POINT(1.0 2.0)",
            "locationName": "Test Reef",
            "temperature": 20.2,
            "visibility": 15.1,
            "notes": "Test observation note",
        }
        if payload_override:
            payload.update(payload_override)
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        resp = client.post(obs_url, payload, format="json")
        assert resp.status_code in (200, 201)
        return resp.data

    def test_profile_me_requires_auth(self, client):
        resp = client.get(self.profile_me_url)
        assert resp.status_code in (401, 403)

    def test_profile_me_no_observations(self, client, register_user):
        # Activate the user first
        user_obj = User.objects.get(email=register_user["email"])
        user_obj.is_active = True
        user_obj.email_verified = True
        user_obj.save()

        login = client.post(
            self.login_url,
            {
                "email": "user@example.com",
                "password": "testpassword123",
            },
            format="json",
        )
        token = login.data["access"]
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        resp = client.get(self.profile_me_url)
        assert resp.status_code == 200
        data = resp.json()
        assert "observation_count" in data
        assert data["observation_count"] == 0
        assert "observations" in data
        features = data["observations"]["features"]
        assert features == []

    def test_profile_me_with_observations(self, client, register_user):
        # Activate the user first
        user_obj = User.objects.get(email=register_user["email"])
        user_obj.is_active = True
        user_obj.email_verified = True
        user_obj.save()

        login = client.post(
            self.login_url,
            {
                "email": "user@example.com",
                "password": "testpassword123",
            },
            format="json",
        )
        token = login.data["access"]
        self.create_observation_for_user(client, token)
        resp = client.get(self.profile_me_url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["observation_count"] == 1
        features = data["observations"]["features"]
        assert len(features) == 1
        obs_props = features[0]["properties"]
        assert obs_props["speciesName"] == "Test Fish"
        assert obs_props["locationName"] == "Test Reef"

    def test_profile_me_multiple_observations(self, client, register_user):
        # Activate the user first
        user_obj = User.objects.get(email=register_user["email"])
        user_obj.is_active = True
        user_obj.email_verified = True
        user_obj.save()

        login = client.post(
            self.login_url,
            {
                "email": "user@example.com",
                "password": "testpassword123",
            },
            format="json",
        )
        token = login.data["access"]
        self.create_observation_for_user(client, token)
        self.create_observation_for_user(
            client, token, payload_override={"speciesName": "Shark"}
        )
        resp = client.get(self.profile_me_url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["observation_count"] == 2
        features = data["observations"]["features"]
        observed_species = [f["properties"]["speciesName"] for f in features]
        assert "Test Fish" in observed_species
        assert "Shark" in observed_species

    def test_password_reset_request_success(self, client, register_user):
        """Test successful password reset request"""
        payload = {"email": "user@example.com"}
        resp = client.post(
            self.password_reset_request_url, payload, format="json"
        )
        assert resp.status_code == 200
        assert resp.data["detail"] == "Password reset email has been sent."

    def test_password_reset_request_invalid_email(self, client):
        """Test password reset request with non-existent email"""
        payload = {"email": "nonexistent@example.com"}
        resp = client.post(
            self.password_reset_request_url, payload, format="json"
        )
        assert resp.status_code == 400
        assert "email" in resp.data

    def test_password_reset_confirm_success(self, client, register_user):
        """Test successful password reset confirmation"""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        # Get user and generate valid token/uid
        # Actually need to get the User model instance
        from django.contrib.auth import get_user_model

        User = get_user_model()
        test_user = User.objects.get(email="user@example.com")

        token = default_token_generator.make_token(test_user)
        uidb64 = urlsafe_base64_encode(force_bytes(str(test_user.pk)))

        payload = {
            "uidb64": uidb64,
            "token": token,
            "new_password": "NewSecurePass123!",
            "re_new_password": "NewSecurePass123!",
        }
        resp = client.post(
            self.password_reset_confirm_url, payload, format="json"
        )
        assert resp.status_code == 200
        assert (
            resp.data["detail"]
            == "Password has been reset with the new password."
        )

        # Verify password actually changed
        test_user.refresh_from_db()
        assert test_user.check_password("NewSecurePass123!")

    def test_password_reset_confirm_invalid_token(self, client, register_user):
        """Test password reset confirmation with invalid token"""
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.auth import get_user_model

        User = get_user_model()
        test_user = User.objects.get(email="user@example.com")

        uidb64 = urlsafe_base64_encode(force_bytes(str(test_user.pk)))

        payload = {
            "uidb64": uidb64,
            "token": "invalid-token-123",
            "new_password": "NewSecurePass123!",
            "re_new_password": "NewSecurePass123!",
        }
        resp = client.post(
            self.password_reset_confirm_url, payload, format="json"
        )
        assert resp.status_code == 400
        assert "token" in resp.data

    def test_password_reset_confirm_invalid_uidb64(self, client):
        """Test password reset confirmation with invalid uidb64"""
        payload = {
            "uidb64": "invalid-uidb64",
            "token": "some-token",
            "new_password": "NewSecurePass123!",
            "re_new_password": "NewSecurePass123!",
        }
        resp = client.post(
            self.password_reset_confirm_url, payload, format="json"
        )
        assert resp.status_code == 400
        assert "uidb64" in resp.data
        assert "Invalid user ID in reset link." in resp.data["uidb64"]

    def test_password_reset_confirm_mismatched_passwords(
        self, client, register_user
    ):
        """Test password reset confirmation with mismatched passwords"""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.auth import get_user_model

        User = get_user_model()
        test_user = User.objects.get(email="user@example.com")

        token = default_token_generator.make_token(test_user)
        uidb64 = urlsafe_base64_encode(force_bytes(str(test_user.pk)))

        payload = {
            "uidb64": uidb64,
            "token": token,
            "new_password": "NewSecurePass123!",
            "re_new_password": "DifferentPassword456!",  # Mismatched
        }
        resp = client.post(
            self.password_reset_confirm_url, payload, format="json"
        )
        assert resp.status_code == 400
        assert "new_password" in resp.data

    def test_password_reset_confirm_password_too_short(
        self, client, register_user
    ):
        """Test password reset confirmation with password too short"""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.auth import get_user_model

        User = get_user_model()
        test_user = User.objects.get(email="user@example.com")

        token = default_token_generator.make_token(test_user)
        uidb64 = urlsafe_base64_encode(force_bytes(str(test_user.pk)))

        payload = {
            "uidb64": uidb64,
            "token": token,
            "new_password": "short",  # Too short (< 8 characters)
            "re_new_password": "short",
        }
        resp = client.post(
            self.password_reset_confirm_url, payload, format="json"
        )
        assert resp.status_code == 400
        assert "new_password" in resp.data or "re_new_password" in resp.data

    @pytest.fixture
    def trusted_email_domain(self):
        from users.models import TrustedEmailDomain

        return TrustedEmailDomain.objects.create(
            domain="example.com",
            organization_name="Test Org",
            auto_approve_to_community=True,
        )

    def test_register_researcher_pending(self, client):
        resp = client.post(
            self.register_url,
            {
                "email": "researcher@example.com",
                "username": "researcherbob",
                "password": "testpassword123",
                "role": User.RESEARCHER_PENDING,
            },
            format="json",
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["email"] == "researcher@example.com"
        assert data["username"] == "researcherbob"
        assert data["role"] == User.RESEARCHER_PENDING

    def test_complete_researcher_profile_success_auto_approve(
        self, client, trusted_email_domain
    ):
        # 1. Register a researcher_pending user
        register_payload = {
            "email": "researcher@example.com",
            "username": "researcherbob",
            "password": "testpassword123",
            "role": User.RESEARCHER_PENDING,
        }
        client.post(self.register_url, register_payload, format="json")

        # Get the user and activate/verify
        user_obj = User.objects.get(email="researcher@example.com")
        user_obj.is_active = True
        user_obj.email_verified = True
        user_obj.save()

        # 2. Login the user to get a token
        login_resp = client.post(
            self.login_url,
            {
                "email": "researcher@example.com",
                "password": "testpassword123",
            },
            format="json",
        )
        token = login_resp.data["access"]
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

        # 3. Complete the researcher profile
        profile_payload = {
            "institution_name": "Test University",
            "research_focus": ["Marine Biology", "Ecology"],
            "years_experience": 5,
        }
        resp = client.patch(
            self.complete_researcher_profile_url,
            profile_payload,
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert (
            data["message"]
            == "Profile completed and automatically verified! You can now"
            " validate observations."
        )

        # 4. Verify user role is updated to RESEARCHER_COMMUNITY
        user_obj.refresh_from_db()
        assert user_obj.role == User.RESEARCHER_COMMUNITY
        assert user_obj.institution_name == "Test University"
        assert user_obj.research_focus == ["Marine Biology", "Ecology"]
        assert user_obj.years_experience == 5

    def test_complete_researcher_profile_missing_fields_fails(self, client):
        # 1. Register a researcher_pending user
        register_payload = {
            "email": "missingfields@example.com",
            "username": "missingfields",
            "password": "testpassword123",
            "role": User.RESEARCHER_PENDING,
        }
        client.post(self.register_url, register_payload, format="json")

        # Get the user and activate/verify
        user_obj = User.objects.get(email="missingfields@example.com")
        user_obj.is_active = True
        user_obj.email_verified = True
        user_obj.save()

        # 2. Login the user to get a token
        login_resp = client.post(
            self.login_url,
            {
                "email": "missingfields@example.com",
                "password": "testpassword123",
            },
            format="json",
        )
        token = login_resp.data["access"]
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

        # 3. Attempt to complete with missing required fields
        profile_payload = {
            "years_experience": (
                2
            ),  # Missing institution_name and research_focus
        }
        resp = client.patch(
            self.complete_researcher_profile_url,
            profile_payload,
            format="json",
        )
        assert resp.status_code == 400
        assert "institution_name" in resp.data
        assert "research_focus" in resp.data

    def test_hobbyist_cannot_complete_researcher_profile(
        self, client, register_user
    ):
        # Activate the hobbyist user
        user_obj = User.objects.get(email=register_user["email"])
        user_obj.is_active = True
        user_obj.email_verified = True
        user_obj.save()

        # Login the hobbyist user
        login_resp = client.post(
            self.login_url,
            {
                "email": register_user["email"],
                "password": "testpassword123",
            },
            format="json",
        )
        token = login_resp.data["access"]
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

        # Attempt to access the researcher profile completion endpoint
        profile_payload = {
            "institution_name": "Should Not Work",
            "research_focus": ["Should Not Work"],
        }
        resp = client.patch(
            self.complete_researcher_profile_url,
            profile_payload,
            format="json",
        )
        assert resp.status_code == 403  # Forbidden
        assert (
            "This endpoint is only for pending researchers."
            in resp.data["detail"]
        )

    def test_profile_me_needs_researcher_profile_completion(self, client):
        # 1. Register a researcher_pending user but do NOT complete profile
        register_payload = {
            "email": "needscompletion@example.com",
            "username": "needscompletion",
            "password": "testpassword123",
            "role": User.RESEARCHER_PENDING,
        }
        client.post(self.register_url, register_payload, format="json")

        # Get the user and activate/verify
        user_obj = User.objects.get(email="needscompletion@example.com")
        user_obj.is_active = True
        user_obj.email_verified = True
        user_obj.save()

        # 2. Login the user to get a token
        login_resp = client.post(
            self.login_url,
            {
                "email": "needscompletion@example.com",
                "password": "testpassword123",
            },
            format="json",
        )
        token = login_resp.data["access"]
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

        # 3. Check profile_me endpoint
        resp = client.get(self.profile_me_url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == User.RESEARCHER_PENDING
        assert data["needs_researcher_profile_completion"] is True

        # After completing the profile, this should become False
        profile_payload = {
            "institution_name": "Completed University",
            "research_focus": ["Oceanography"],
        }
        client.patch(
            self.complete_researcher_profile_url,
            profile_payload,
            format="json",
        )

        resp_after_completion = client.get(self.profile_me_url)
        assert resp_after_completion.status_code == 200
        data_after_completion = resp_after_completion.json()
        assert (
            data_after_completion["needs_researcher_profile_completion"]
            is False
        )
