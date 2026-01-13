from django.contrib import admin

from .models import CuratedObservation


@admin.register(CuratedObservation)
class CuratedObservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "species_name",
        "common_name",
        "occurrence_id",
        "observation_date",
        "observation_datetime",
        "location",
        "location_name",
        "machine_observation",
        "validated",
        "source",
        "depth_min",
        "depth_max",
        "bathymetry",
        "temperature",
        "visibility",
        "notes",
        "sex",
        "image",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "source",
        "validated",
        "observation_date",
        "machine_observation",
        "common_name",
        "species_name",
    )
    search_fields = (
        "species_name",
        "common_name",
        "location_name",
        "notes",
        "occurrence_id",
    )
    readonly_fields = (
        "id",
        "species_name",
        "common_name",
        "occurrence_id",
        "observation_date",
        "observation_datetime",
        "location",
        "location_name",
        "machine_observation",
        "validated",
        "source",
        "depth_min",
        "depth_max",
        "bathymetry",
        "temperature",
        "visibility",
        "notes",
        "sex",
        "image",
        "dataset_name",
        "created_at",
        "updated_at",
    )
