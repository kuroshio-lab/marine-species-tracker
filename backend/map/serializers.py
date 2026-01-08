# backend/map/serializers.py
from observations.models import Observation
from species.models import CuratedObservation
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer


class ObservationGeoSerializer(GeoFeatureModelSerializer):
    speciesName = serializers.CharField(source="species_name")
    locationName = serializers.CharField(source="location_name")
    observationDatetime = serializers.DateTimeField(
        source="observation_datetime"
    )
    commonName = serializers.CharField(
        source="common_name", allow_null=True, required=False
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
    notes = serializers.CharField(allow_null=True, required=False)
    image = serializers.ImageField(allow_null=True, required=False)
    sex = serializers.CharField(allow_null=True, required=False)
    userId = serializers.PrimaryKeyRelatedField(
        source="user.id", read_only=True
    )
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Observation
        geo_field = "location"
        fields = (
            "id",
            "speciesName",
            "commonName",
            "location",
            "observationDatetime",
            "locationName",
            "source",
            "image",
            "depthMin",
            "depthMax",
            "bathymetry",
            "temperature",
            "visibility",
            "notes",
            "sex",
            "validated",
            "userId",
            "createdAt",
            "updatedAt",
        )


class CuratedObservationGeoSerializer(GeoFeatureModelSerializer):
    speciesName = serializers.CharField(source="species_name")
    commonName = serializers.CharField(source="common_name")
    locationName = serializers.CharField(source="location_name")
    machineObservation = serializers.CharField(source="machine_observation")
    observationDatetime = serializers.DateTimeField(
        source="observation_datetime"
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
    notes = serializers.CharField(allow_null=True, required=False)
    image = serializers.URLField(allow_null=True, required=False)
    sex = serializers.CharField(allow_null=True, required=False)
    occurrenceId = serializers.CharField(
        source="occurrence_id", allow_null=True, required=False
    )

    class Meta:
        model = CuratedObservation
        geo_field = "location"
        fields = (
            "id",
            "speciesName",
            "commonName",
            "location",
            "observationDatetime",
            "locationName",
            "machineObservation",
            "source",
            "image",
            "depthMin",
            "depthMax",
            "bathymetry",
            "temperature",
            "visibility",
            "notes",
            "sex",
            "validated",
        )


class MapCuratedObservationSerializer(GeoFeatureModelSerializer):
    id = serializers.SerializerMethodField()
    speciesName = serializers.CharField(source="species_name")
    commonName = serializers.CharField(source="common_name", allow_null=True)
    locationName = serializers.CharField(source="location_name")
    machineObservation = serializers.CharField(source="machine_observation")
    observationDatetime = serializers.DateTimeField(
        source="observation_datetime"
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
    notes = serializers.CharField(allow_null=True, required=False)
    image = serializers.URLField(allow_null=True, required=False)
    sex = serializers.CharField(allow_null=True, required=False)
    occurrenceId = serializers.CharField(
        source="occurrence_id", allow_null=True, required=False
    )

    class Meta:
        model = CuratedObservation
        geo_field = "location"
        fields = (
            "id",
            "speciesName",
            "commonName",
            "location",
            "observationDatetime",
            "locationName",
            "machineObservation",
            "source",
            "source",
            "image",
            "depthMin",
            "depthMax",
            "bathymetry",
            "temperature",
            "visibility",
            "notes",
            "sex",
            "validated",
            "occurrenceId",
        )

    def get_id(self, obj):
        return f"external-{obj.id}"


class MapObservationSerializer(GeoFeatureModelSerializer):
    source = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    machineObservation = serializers.SerializerMethodField()
    speciesName = serializers.CharField(source="species_name")
    commonName = serializers.CharField(source="common_name", allow_null=True)
    locationName = serializers.CharField(source="location_name")
    observationDatetime = serializers.DateTimeField(
        source="observation_datetime"
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
    notes = serializers.CharField(allow_null=True, required=False)
    image = serializers.ImageField(allow_null=True, required=False)
    sex = serializers.CharField(allow_null=True, required=False)
    userId = serializers.PrimaryKeyRelatedField(
        source="user.id", read_only=True
    )
    username = serializers.CharField(
        source="user.username", read_only=True, allow_null=True
    )
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Observation
        geo_field = "location"
        fields = (
            "id",
            "speciesName",
            "commonName",
            "location",
            "observationDatetime",
            "locationName",
            "machineObservation",
            "source",
            "image",
            "depthMin",
            "depthMax",
            "bathymetry",
            "temperature",
            "visibility",
            "notes",
            "sex",
            "validated",
            "userId",
            "username",
            "createdAt",
            "updatedAt",
        )

    def get_source(self, obj):
        return "user"

    def get_id(self, obj):
        return f"user-{obj.id}"

    def get_machineObservation(self, obj):
        return "User Observation"
