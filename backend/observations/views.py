import json

from django.http import HttpResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_gis.filters import InBBoxFilter

from .models import Observation
from .permissions import IsVerifiedResearcher
from .serializers import ObservationExportSerializer, ObservationGeoSerializer


class ObservationListCreateView(generics.ListCreateAPIView):
    serializer_class = ObservationGeoSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Observation.objects.all()
    filter_backends = (InBBoxFilter,)
    bbox_filter_field = "location"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        return Observation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Detail
class ObservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Observation.objects.all()
    serializer_class = ObservationGeoSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedResearcher,
    ]

    def get_queryset(self):
        # Only allow the owner (or admin/researcher) to view/update/delete
        user = self.request.user
        if user.is_staff or getattr(user, "role", None) == "researcher":
            return Observation.objects.all()
        return Observation.objects.filter(user=user)


# Export
class ObservationExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = Observation.objects.filter(user=request.user)

        species_name = request.GET.get("species_name")
        common_name = request.GET.get("common_name")
        min_date = request.GET.get("min_date")
        max_date = request.GET.get("max_date")

        if species_name:
            queryset = queryset.filter(species_name__iexact=species_name)
        if common_name:
            queryset = queryset.filter(common_name__iexact=common_name)
        if min_date:
            queryset = queryset.filter(observation_datetime__gte=min_date)
        if max_date:
            queryset = queryset.filter(observation_datetime__lte=max_date)

        serializer = ObservationExportSerializer(
            queryset, many=True, context={"request": request}
        )

        response = HttpResponse(
            json.dumps(serializer.data),
            content_type="application/json",
        )
        response["Content-Disposition"] = (
            'attachment; filename="marine_observations_export.json"'
        )
        return response


# Only admin/researcher can validate
class ObservationValidateView(APIView):
    permission_classes = [IsVerifiedResearcher]

    def post(self, request, pk):
        try:
            obs = Observation.objects.get(pk=pk)
        except Observation.DoesNotExist:
            return Response({"detail": "Observation not found."}, status=404)

        obs.validated = "validated"
        obs.save()
        return Response(ObservationGeoSerializer(obs).data)


class CuratedObservationListView(generics.ListAPIView):
    serializer_class = ObservationGeoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Observation.objects.filter(source="obis")
