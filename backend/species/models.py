# species/models.py
from django.contrib.gis.db import models


class CuratedObservation(models.Model):
    # Universal identifier for cross-API deduplication (Darwin Core standard)
    occurrence_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Darwin Core occurrenceID - unique across OBIS/GBIF",
        null=True,
        blank=True,
    )

    # Display essentials (ALL REQUIRED for quality)
    species_name = models.CharField(max_length=255)
    common_name = models.CharField(max_length=255, blank=True, null=True)
    observation_date = models.DateField()  # REQUIRED
    observation_datetime = models.DateTimeField(blank=True, null=True)
    location = models.PointField(geography=True)  # REQUIRED (PostGIS)

    # Observation detail
    location_name = models.CharField(max_length=512, blank=True, null=True)
    machine_observation = models.CharField(
        max_length=128, blank=True, null=True
    )
    validated = models.CharField(max_length=128, blank=True, null=True)

    # Scientific/Environmental info
    depth_min = models.FloatField(blank=True, null=True)
    depth_max = models.FloatField(blank=True, null=True)
    bathymetry = models.FloatField(blank=True, null=True)

    # Optional environmental data
    temperature = models.FloatField(blank=True, null=True)
    visibility = models.FloatField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Media/info
    image = models.URLField(blank=True, null=True)

    sex = models.CharField(
        max_length=10,
        choices=[
            ("male", "Male"),
            ("female", "Female"),
            ("unknown", "Unknown"),
        ],
        default="unknown",
        blank=True,
        null=True,
    )

    # Provenance tracking
    source = models.CharField(
        max_length=20,
        choices=[
            ("OBIS", "OBIS Direct"),
            ("GBIF", "GBIF Direct"),
            ("BOTH", "Both APIs"),
        ],
        default="OBIS",
        db_index=True,
    )
    dataset_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["-observation_date"]
        indexes = [
            models.Index(fields=["occurrence_id"]),
            models.Index(fields=["source"]),
            models.Index(fields=["-observation_date"]),
            models.Index(fields=["species_name"]),
        ]

    def __str__(self):
        return f"{self.species_name} ({self.observation_date})"
