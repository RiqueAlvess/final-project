"""Admin configuration for tenants."""

from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Tenant, Domain


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1
    fields = ('domain', 'is_primary')


@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'schema_name', 'cnpj', 'responsible_email', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'cnpj', 'schema_name', 'responsible_email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [DomainInline]

    fieldsets = (
        ('Company Information', {
            'fields': ('name', 'cnpj', 'cnae', 'responsible_email')
        }),
        ('Technical', {
            'fields': ('schema_name', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('domain', 'tenant__name')
    raw_id_fields = ('tenant',)
