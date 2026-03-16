"""Tenant models for multi-tenant SaaS platform."""

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Tenant(TenantMixin):
    """
    Represents a company/organization in the multi-tenant system.
    Each tenant has its own isolated PostgreSQL schema.
    """

    name = models.CharField(max_length=200, verbose_name='Company Name')
    cnpj = models.CharField(max_length=18, unique=True, verbose_name='CNPJ')
    cnae = models.CharField(max_length=10, verbose_name='CNAE')
    responsible_email = models.EmailField(verbose_name='Responsible Email')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # django-tenants required: auto creates schema when saving
    auto_create_schema = True
    auto_drop_schema = True

    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} ({self.schema_name})'


class Domain(DomainMixin):
    """
    Maps domains to tenants.
    Example: empresa1.sistema.com -> Tenant(schema_name='empresa1')
    """

    class Meta:
        verbose_name = 'Domain'
        verbose_name_plural = 'Domains'

    def __str__(self) -> str:
        return f'{self.domain} -> {self.tenant.name}'
