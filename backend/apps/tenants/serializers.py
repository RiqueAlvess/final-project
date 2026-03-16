"""Serializers for tenant models."""

from rest_framework import serializers
from .models import Tenant, Domain


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ('id', 'domain', 'is_primary')


class TenantSerializer(serializers.ModelSerializer):
    domains = DomainSerializer(many=True, read_only=True)

    class Meta:
        model = Tenant
        fields = ('id', 'name', 'cnpj', 'cnae', 'responsible_email', 'schema_name', 'is_active', 'domains', 'created_at')
        read_only_fields = ('schema_name', 'created_at')


class TenantPublicSerializer(serializers.ModelSerializer):
    """Public info about the current tenant (no sensitive data)."""

    class Meta:
        model = Tenant
        fields = ('id', 'name', 'cnpj', 'cnae')
