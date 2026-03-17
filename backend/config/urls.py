"""Root URL configuration for multi-tenant SaaS platform."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Authentication
    path('api/auth/', include('apps.authentication.urls')),

    # Users
    path('api/users/', include('apps.users.urls')),

    # Core
    path('api/', include('apps.core.urls')),

    # Organizational
    path('api/organizational/', include('apps.organizational.urls')),

    # Campaigns & HSE-IT survey
    path('api/campaigns/', include('apps.campaigns.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
