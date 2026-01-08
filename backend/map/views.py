# backend/map/views.py

import math
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from observations.models import Observation
from species.models import CuratedObservation

from .serializers import (
    MapObservationSerializer,
    MapCuratedObservationSerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def map_observations(request):
    """
    Geo-filtered observations for the map with pagination and ratio limits.
    Params:
        ?lat=<latitude>&lng=<longitude>&radius=<km> (for geographic filtering)
        ?limit=<number> (total number of observations to return)
        ?offset=<number> (starting index for pagination)
    """
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius")
    limit = int(
        request.GET.get("limit", settings.MAP_OBSERVATION_DEFAULT_LIMIT)
    )
    offset = int(request.GET.get("offset", 0))
    species_name = request.GET.get("species_name")
    common_name = request.GET.get("common_name")
    min_date = request.GET.get("min_date")
    max_date = request.GET.get("max_date")

    user_observations_queryset = Observation.objects.all()
    # Filter out CuratedObservations with null locations
    curated_species_queryset = CuratedObservation.objects.exclude(
        location__isnull=True
    )

    if species_name:
        user_observations_queryset = user_observations_queryset.filter(
            species_name__iexact=species_name
        )
        curated_species_queryset = curated_species_queryset.filter(
            species_name__iexact=species_name
        )

    if common_name:
        user_observations_queryset = user_observations_queryset.filter(
            common_name__iexact=common_name
        )
        curated_species_queryset = curated_species_queryset.filter(
            common_name__iexact=common_name
        )

    if min_date:
        user_observations_queryset = user_observations_queryset.filter(
            observation_datetime__gte=min_date
        )
        curated_species_queryset = curated_species_queryset.filter(
            observation_date__gte=min_date
        )

    if max_date:
        user_observations_queryset = user_observations_queryset.filter(
            observation_datetime__lte=max_date
        )
        curated_species_queryset = curated_species_queryset.filter(
            observation_date__lte=max_date
        )

    if lat and lng:
        try:
            lat, lng = float(lat), float(lng)
            point = Point(
                float(lng), float(lat), srid=4326
            )  # Note order: lng, lat!

            # Apply geo-filtering
            if radius:
                radius = float(radius)
                distance_filter = D(km=radius)
                user_observations_queryset = user_observations_queryset.filter(
                    location__distance_lte=(point, distance_filter)
                )
                curated_species_queryset = curated_species_queryset.filter(
                    location__distance_lte=(point, distance_filter)
                )

            # Annotate with distance and order by distance from the center point
            user_observations_queryset = user_observations_queryset.annotate(
                distance=Distance("location", point)
            ).order_by("distance")
            curated_species_queryset = curated_species_queryset.annotate(
                distance=Distance("location", point)
            ).order_by("distance")

        except (TypeError, ValueError) as e:
            print(f"Error in geo-filtering parameters: {e}")
            return Response(
                {"detail": "Invalid latitude/longitude/radius."}, status=400
            )
        except Exception as e:
            print(f"Unexpected error during geo-filtering: {e}")
            return Response(
                {
                    "detail": (
                        "An unexpected error occurred during geo-filtering."
                    )
                },
                status=500,
            )
    else:
        # Default ordering if no lat/lng for geographic ordering
        user_observations_queryset = user_observations_queryset.order_by(
            "-created_at"
        )
        curated_species_queryset = curated_species_queryset.order_by(
            "-observation_date"
        )

    try:
        # Apply ratio and limit
        user_limit = math.ceil(limit * settings.MAP_OBSERVATION_USER_RATIO)
        curated_limit = limit - user_limit

        # Apply offset and limit to the querysets
        user_observations_list = list(
            user_observations_queryset[offset : offset + user_limit]
        )
        curated_species_list = list(
            curated_species_queryset[offset : offset + curated_limit]
        )

        # Serialize
        user_serializer = MapObservationSerializer(
            user_observations_list, many=True
        )
        curated_serializer = MapCuratedObservationSerializer(
            curated_species_list, many=True
        )

        # Combine features
        combined_features = (
            user_serializer.data["features"]
            + curated_serializer.data["features"]
        )

        return Response(
            {"type": "FeatureCollection", "features": combined_features}
        )
    except Exception as e:
        print(f"Error during serialization or response generation: {e}")
        return Response(
            {"detail": "An error occurred while processing map observations."},
            status=500,
        )
