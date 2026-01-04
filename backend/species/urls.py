from django.urls import path

from .views import CuratedObservationList, SpeciesSearchView

urlpatterns = [
    path(
        "curated/",
        CuratedObservationList.as_view(),
        name="curated-observation-list",
    ),
    path(
        "search/",
        SpeciesSearchView.as_view(),
        name="species-search",
    ),
]
