from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Observation


class ObservationGeoSerializer(GeoFeatureModelSerializer):
    # Explicitly define fields that should be writable
    speciesName = serializers.CharField(source="species_name", max_length=100)
    commonName = serializers.CharField(
        source="common_name", max_length=255, allow_null=True, required=False
    )
    locationName = serializers.CharField(
        source="location_name", max_length=255
    )
    observationDatetime = serializers.DateTimeField(
        source="observation_datetime",
        format="%Y-%m-%dT%H:%M:%SZ",
        input_formats=[
            "%Y-%m-%dT%H:%M",  # For datetime-local input without seconds
            "%Y-%m-%dT%H:%M:%SZ",  # For ISO without milliseconds
            "%Y-%m-%dT%H:%M:%S.%fZ",  # **FIX: For ISO with milliseconds and Z (UTC)**
            "%Y-%m-%dT%H:%M:%S.%f",  # For ISO with milliseconds, no Z (local/naive)
            "%Y-%m-%dT%H:%M:%S",  # For ISO without milliseconds and Z
        ],
        write_only=False,
        allow_null=False,
        required=True,
    )
    depthMin = serializers.FloatField(
        source="depth_min", allow_null=True, required=False
    )
    depthMax = serializers.FloatField(
        source="depth_max", allow_null=True, required=False
    )

    bathymetry = serializers.FloatField(allow_null=True, required=False)
    temperature = serializers.FloatField(allow_null=True, required=False)
    visibility = serializers.FloatField(allow_null=True, required=False)
    notes = serializers.CharField(
        allow_blank=True, required=False, allow_null=True
    )
    sex = serializers.ChoiceField(
        choices=Observation.SEX_CHOICES, allow_null=True, required=False
    )
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Observation
        geo_field = "location"
        fields = (
            "id",
            "speciesName",
            "commonName",
            "observationDatetime",
            "location",
            "locationName",
            "depthMin",
            "depthMax",
            "bathymetry",
            "temperature",
            "image",
            "visibility",
            "notes",
            "validated",
            "source",
            "user",
            "sex",
        )

    read_only_fields = (
        "source",
        "validated",
        "created_at",
        "updated_at",
        "image",
    )

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        # Prevent hobbyist from updating 'validated' field
        if "validated" in validated_data:
            if not user or not (
                user.is_staff or getattr(user, "role", None) == "researcher"
            ):
                raise serializers.ValidationError(
                    {
                        "validated": (
                            "You do not have permission to validate"
                            " observations."
                        )
                    }
                )
        updated_instance = super().update(instance, validated_data)
        updated_instance.save()

        return updated_instance


class ObservationExportSerializer(ObservationGeoSerializer):
    """
    Slimmed-down serializer for the JSON export.
    Identical to ObservationGeoSerializer except the internal `user` ID is
    omitted — it is redundant (every record in the file belongs to the
    requesting user) and leaks an internal database identifier.
    """

    class Meta(ObservationGeoSerializer.Meta):
        fields = (
            "id",
            "speciesName",
            "commonName",
            "observationDatetime",
            "location",
            "locationName",
            "depthMin",
            "depthMax",
            "bathymetry",
            "temperature",
            "image",
            "visibility",
            "notes",
            "validated",
            "source",
            "sex",
        )
