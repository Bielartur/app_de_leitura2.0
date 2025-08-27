from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("/", include("livros.urls", namespace="livros")),
    path("contas/", include("contas.urls")),
] + static(settings.STATIC_URL, document_root=getattr(settings, "STATIC_ROOT", None))
