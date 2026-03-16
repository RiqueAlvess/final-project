"""AppConfig for organizational module."""

from django.apps import AppConfig


class OrganizationalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.organizational'
    verbose_name = 'Organizational'
