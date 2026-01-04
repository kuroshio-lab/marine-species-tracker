from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from .models import CuratedObservation
from .serializers import CuratedObservationSerializer


class CuratedObservationList(generics.ListAPIView):
    queryset = CuratedObservation.objects.all().order_by(
        "-observation_datetime"
    )
    serializer_class = CuratedObservationSerializer
    # Optional: add filters or search here
    # filter_backends = [DjangoFilterBackend, SearchFilter]
    # filterset_fields = ['species_name', 'source', 'observation_date']
    # search_fields = ['species_name', 'common_name', 'location_name']


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
