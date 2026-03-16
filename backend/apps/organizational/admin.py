"""Admin configuration for organizational module."""

from django.contrib import admin

from .models import CSVImport, LeaderPermission, Registro, Setor, Unidade


class SetorInline(admin.TabularInline):
    model = Setor
    extra = 0
    fields = ('name',)


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ('name', 'setor_count', 'created_at')
    search_fields = ('name',)
    inlines = (SetorInline,)

    def setor_count(self, obj: Unidade) -> int:
        return obj.setores.count()

    setor_count.short_description = 'Setores'


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('name', 'unidade', 'created_at')
    list_filter = ('unidade',)
    search_fields = ('name', 'unidade__name')


class RegistroInline(admin.TabularInline):
    model = Registro
    extra = 0
    fields = ('email', 'unidade', 'setor')
    readonly_fields = ('email', 'unidade', 'setor')
    can_delete = False
    max_num = 0


@admin.register(CSVImport)
class CSVImportAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'status', 'total_rows', 'successful_rows', 'failed_rows', 'imported_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('file_name', 'imported_by__email')
    readonly_fields = ('file_name', 'status', 'total_rows', 'successful_rows', 'failed_rows', 'errors', 'imported_by', 'created_at')
    inlines = (RegistroInline,)


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = ('email', 'unidade', 'setor', 'created_at')
    list_filter = ('unidade', 'setor')
    search_fields = ('email', 'unidade__name', 'setor__name')


@admin.register(LeaderPermission)
class LeaderPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'unidade', 'setor')
    list_filter = ('unidade', 'setor')
    search_fields = ('user__email', 'unidade__name', 'setor__name')
    raw_id_fields = ('user',)
