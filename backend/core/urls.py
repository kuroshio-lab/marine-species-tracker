from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse


def health_check(request):
    return HttpResponse("ok")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check),
    path("api/v1/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
