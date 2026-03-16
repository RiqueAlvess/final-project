"""Core URL patterns."""

from django.urls import path
from .views import health_check, tenant_info, dashboard_stats

app_name = 'core'

urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('tenant/', tenant_info, name='tenant-info'),
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
]
