import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CuratedObservation
from .serializers import CuratedObservationSerializer


class CuratedObservationFilter(django_filters.FilterSet):
    min_date = django_filters.DateTimeFilter(
        field_name="observation_datetime", lookup_expr="gte"
    )
    max_date = django_filters.DateTimeFilter(
        field_name="observation_datetime", lookup_expr="lte"
    )

    class Meta:
        model = CuratedObservation
        fields = ["species_name", "common_name", "min_date", "max_date"]


class CuratedObservationList(generics.ListAPIView):
    queryset = CuratedObservation.objects.all().order_by(
        "-observation_datetime"
    )
    serializer_class = CuratedObservationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CuratedObservationFilter
    search_fields = ["species_name", "common_name"]


class SpeciesSearchView(APIView):
    """
    Search endpoint for species by scientific name or common name.
    Returns distinct species matching the search query.
    """

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response([])

        # Search in both species_name and common_name (case-insensitive)
        # Get distinct species by grouping on species_name and common_name
        queryset = (
            CuratedObservation.objects.filter(
                Q(species_name__icontains=query)
                | Q(common_name__icontains=query)
            )
            .values("species_name", "common_name")
            .distinct()
            .order_by("species_name")[:20]  # Limit to 20 results
        )

        # Format the response
        results = [
            {
                "speciesName": item["species_name"],
                "commonName": item["common_name"] or "",
            }
            for item in queryset
        ]

        return Response(results)
