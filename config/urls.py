"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/master/', include('master.urls')),
    path("api/usermanagement/", include("usermanagement.urls")),
    path("api/feeder/", include("feeder.urls")),
    path("debtors/", include("debtors.urls")),
    path('api/clientmaster/', include('clientmaster.urls')),
    path('api/installation/', include('installation.urls')),
    path('api/collection/', include('collection.urls')),
    path("api/", include("claims.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)