from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import CuratedObservation


class CuratedObservationSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = CuratedObservation
        geo_field = "location"
        fields = (
            "id",
            "species_name",
            "common_name",
            "observation_date",
            "observation_datetime",
            "location",
            "location_name",
            "machine_observation",
            "validated",
            "source",
            "depth_min",
            "depth_max",
            "temperature",
            "visibility",
            "notes",
            "image",
            "dataset_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
