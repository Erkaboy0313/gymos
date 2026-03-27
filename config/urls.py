from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language
from users.views import initial

urlpatterns = [
    path('',initial),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/users/", include("users.urls")),
    path("api/branches/", include("branches.urls")),
    path("api/subscriptions/", include("subscriptions.urls")),
    path("api/identifiers/", include("identifiers.urls")),
    path("api/devices/", include("devices.urls")),
    path("api/access/", include("access.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/tg/", include("telegram_bot.urls")),
    path("i18n/setlang/", set_language, name="set_language"),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)