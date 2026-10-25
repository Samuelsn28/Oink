from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("", include("financas.urls")),
    path("", include("oink.urls")),
    path("contas/", include("contas.urls")),
    path("contas/", include("django.contrib.auth.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
