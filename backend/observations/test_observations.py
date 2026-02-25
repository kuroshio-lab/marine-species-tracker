import datetime

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from observations.models import Observation
from users.models import TrustedEmailDomain

User = get_user_model()


class ObservationAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            username="usertest",
            password="StrongPassword123",
        )
        # Activate the user for login
        self.user.is_active = True
        self.user.email_verified = True
        self.user.save()
        # Create a trusted email domain for auto-approval tests
        TrustedEmailDomain.objects.create(
            domain="test.com",
            organization_name="Test Organization",
            auto_approve_to_community=True,
        )

        self.login_url = reverse("token_obtain_pair")
        self.observations_url = reverse("user-observations")

    def authenticate(self):
        response = self.client.post(
            self.login_url,
            {
                "email": "user@test.com",
                "password": "StrongPassword123",
            },
            format="json",
        )
        token = response.data.get("access")
        assert (
            token is not None
        ), f"Login failed or no token. Response data: {response.data}"
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    def test_auth_required_for_observation_list_create(self):
        response = self.client.get(self.observations_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
        response = self.client.post(self.observations_url, {})
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_create_observation(self):
        self.authenticate()
        data = {
            "speciesName": "Shark",
            "location": {"type": "Point", "coordinates": [52.505, 14.404]},
            "observationDatetime": "2025-10-21T13:45:00Z",
            "locationName": "Pacific Point",
            "temperature": 20.5,
            "visibility": 10,
            "notes": "Saw dorsal fin.",
        }
        response = self.client.post(self.observations_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Observation.objects.count(), 1)
        obs = Observation.objects.get()
        self.assertEqual(obs.species_name, "Shark")
        self.assertEqual(obs.user, self.user)

    def test_list_observations_returns_only_user_observations(self):
        self.authenticate()
        Observation.objects.create(
            user=self.user,
            species_name="Whale",
            location=Point(4.56, 1.23),
            observation_datetime=datetime.datetime.now(datetime.timezone.utc),
            location_name="Deep Bay",
            depth_min=100,
            temperature=3.5,
            visibility=25,
            notes="Big splash",
        )
        response = self.client.get(self.observations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        features = response.data["results"]["features"]
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0]["properties"]["speciesName"], "Whale")

    def test_missing_required_fields_fails(self):
        self.authenticate()
        data = {"speciesName": "", "latitude": "", "longitude": ""}
        response = self.client.post(self.observations_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def create_user_with_role(
        self, email, username, password, role=None, is_staff=False
    ):
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            role=role or User.HOBBYIST,
            is_active=True,
            email_verified=True,
        )
        if role:
            user.role = role
        user.is_staff = is_staff
        user.save()
        return user

    def authenticate_as(self, user):
        response = self.client.post(
            self.login_url,
            {
                "email": user.email,
                "username": user.username,
                "password": "StrongPassword123",
            },
            format="json",
        )
        token = response.data.get("access")
        assert (
            token is not None
        ), f"Login failed or no token. Response data: {response.data}"
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    def make_observation(self, user=None):
        return Observation.objects.create(
            user=user or self.user,
            species_name="Dolphin",
            location=Point(0, 0),
            observation_datetime=datetime.datetime.now(datetime.timezone.utc),
            location_name="Blue Sea",
            depth_min=15,
            temperature=21,
            visibility=30,
            notes="note",
        )

    def test_hobbyist_cannot_validate_observation(self):
        self.authenticate()
        obs = self.make_observation(self.user)
        url = reverse("observation-validate", kwargs={"pk": obs.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        obs.refresh_from_db()
        self.assertNotEqual(obs.validated, "validated")

    def test_admin_can_validate_observation(self):
        admin_user = self.create_user_with_role(
            email="admin@test.com",
            username="admintest",
            password="StrongPassword123",
            is_staff=True,
        )
        obs = self.make_observation(admin_user)
        self.authenticate_as(admin_user)
        url = reverse("observation-validate", kwargs={"pk": obs.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        obs.refresh_from_db()
        self.assertEqual(obs.validated, "validated")

    def test_researcher_community_can_validate_after_profile_completion(self):
        # Create a pending researcher
        researcher_user = self.create_user_with_role(
            email="researcher@test.com",
            username="researchertest",
            password="StrongPassword123",
            role=User.RESEARCHER_PENDING,
        )

        from users.serializers import ResearcherProfileSerializer

        serializer = ResearcherProfileSerializer(
            instance=researcher_user,
            data={
                "institution_name": "Test University",
                "research_focus": ["fish"],
            },
            partial=True,
        )
        self.assertTrue(serializer.is_valid(raise_exception=True))
        serializer.save()

        researcher_user.refresh_from_db()

        self.assertEqual(researcher_user.role, User.RESEARCHER_COMMUNITY)

    def test_researcher_pending_uncompleted_profile_cannot_validate(self):
        pending_researcher_user = self.create_user_with_role(
            email="pending@test.com",
            username="pendingresearcher",
            password="StrongPassword123",
            role=User.RESEARCHER_PENDING,
        )
        self.assertEqual(pending_researcher_user.role, User.RESEARCHER_PENDING)

        obs = self.make_observation(pending_researcher_user)
        self.authenticate_as(pending_researcher_user)
        url = reverse("observation-validate", kwargs={"pk": obs.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        obs.refresh_from_db()
        self.assertNotEqual(obs.validated, "validated")

    def test_researcher_institutional_can_validate_observation(self):
        institutional_researcher_user = self.create_user_with_role(
            email="institutional@test.com",
            username="institutionalresearcher",
            password="StrongPassword123",
            role=User.RESEARCHER_INSTITUTIONAL,
        )
        self.assertEqual(
            institutional_researcher_user.role, User.RESEARCHER_INSTITUTIONAL
        )

        obs = self.make_observation(institutional_researcher_user)
        self.authenticate_as(institutional_researcher_user)
        url = reverse("observation-validate", kwargs={"pk": obs.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        obs.refresh_from_db()
        self.assertEqual(obs.validated, "validated")

    def test_validate_nonexistent_observation_returns_404(self):
        admin_user = self.create_user_with_role(
            email="admin2@test.com",
            username="admintest2",
            password="StrongPassword123",
            is_staff=True,
        )
        self.authenticate_as(admin_user)
        url = reverse("observation-validate", kwargs={"pk": 9999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class ObservationExportTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="exporter@test.com",
            username="exportertest",
            password="StrongPassword123",
            is_active=True,
            email_verified=True,
        )
        TrustedEmailDomain.objects.create(
            domain="test.com",
            organization_name="Test Organization",
            auto_approve_to_community=True,
        )
        self.login_url = reverse("token_obtain_pair")
        self.export_url = reverse("observation-export")

    def authenticate(self):
        response = self.client.post(
            self.login_url,
            {"email": "exporter@test.com", "password": "StrongPassword123"},
            format="json",
        )
        token = response.data.get("access")
        assert token is not None, f"Login failed. Response: {response.data}"
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    def make_observation(
        self, user=None, species_name="Dolphin", observation_datetime=None
    ):
        return Observation.objects.create(
            user=user or self.user,
            species_name=species_name,
            location=Point(0, 0),
            observation_datetime=observation_datetime
            or datetime.datetime.now(datetime.timezone.utc),
            location_name="Blue Sea",
            depth_min=15,
            temperature=21,
            visibility=30,
            notes="note",
        )

    def test_export_requires_auth(self):
        response = self.client.get(self.export_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_export_returns_attachment(self):
        self.authenticate()
        response = self.client.get(self.export_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("attachment", response.get("Content-Disposition", ""))
        self.assertIn("application/json", response.get("Content-Type", ""))

    def test_export_contains_geojson_feature_collection(self):
        self.authenticate()
        self.make_observation()
        response = self.client.get(self.export_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        import json as json_module

        data = json_module.loads(response.content)
        self.assertEqual(data.get("type"), "FeatureCollection")
        self.assertIn("features", data)
        self.assertIsInstance(data["features"], list)

    def test_export_only_returns_own_observations(self):
        self.authenticate()
        other_user = User.objects.create_user(
            email="other@test.com",
            username="otheruser",
            password="StrongPassword123",
            is_active=True,
            email_verified=True,
        )
        self.make_observation(user=self.user, species_name="Whale")
        self.make_observation(user=other_user, species_name="Shark")
        response = self.client.get(self.export_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        import json as json_module

        data = json_module.loads(response.content)
        self.assertEqual(len(data["features"]), 1)
        self.assertEqual(
            data["features"][0]["properties"]["speciesName"], "Whale"
        )

    def test_export_respects_species_name_filter(self):
        self.authenticate()
        self.make_observation(species_name="Dolphin")
        self.make_observation(species_name="Shark")
        response = self.client.get(
            self.export_url, {"species_name": "Dolphin"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        import json as json_module

        data = json_module.loads(response.content)
        self.assertEqual(len(data["features"]), 1)
        self.assertEqual(
            data["features"][0]["properties"]["speciesName"], "Dolphin"
        )

    def test_export_respects_date_filters(self):
        self.authenticate()
        early = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        late = datetime.datetime(2025, 6, 1, tzinfo=datetime.timezone.utc)
        self.make_observation(species_name="Early", observation_datetime=early)
        self.make_observation(species_name="Late", observation_datetime=late)

        response = self.client.get(
            self.export_url,
            {"min_date": "2025-01-01", "max_date": "2025-12-31"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        import json as json_module

        data = json_module.loads(response.content)
        self.assertEqual(len(data["features"]), 1)
        self.assertEqual(
            data["features"][0]["properties"]["speciesName"], "Late"
        )
