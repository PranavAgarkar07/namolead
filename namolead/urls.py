from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve as media_serve
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("", include(("opportunities.urls", "opportunities"), namespace="opportunities")),
    path("", include(("tracking.urls", "tracking"), namespace="tracking")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        path("media/<path:path>", media_serve, {"document_root": settings.MEDIA_ROOT})
    ]

urlpatterns += [path("", include(wagtail_urls))]
