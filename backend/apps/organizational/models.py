"""Organizational hierarchy models: Unidade, Setor, Registro, CSVImport, LeaderPermission."""

from django.conf import settings
from django.db import models


class Unidade(models.Model):
    """Business unit within a tenant."""

    name = models.CharField(max_length=200, verbose_name='Name')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Unidade'
        verbose_name_plural = 'Unidades'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Setor(models.Model):
    """Department/sector belonging to a Unidade."""

    name = models.CharField(max_length=200, verbose_name='Name')
    unidade = models.ForeignKey(
        Unidade,
        on_delete=models.CASCADE,
        related_name='setores',
        verbose_name='Unidade',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'
        ordering = ['unidade__name', 'name']
        unique_together = ('name', 'unidade')

    def __str__(self) -> str:
        return f'{self.unidade.name} / {self.name}'


class CSVImport(models.Model):
    """Tracks a CSV file import operation."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    file_name = models.CharField(max_length=255, verbose_name='File Name')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Status',
    )
    total_rows = models.PositiveIntegerField(default=0, verbose_name='Total Rows')
    successful_rows = models.PositiveIntegerField(default=0, verbose_name='Successful Rows')
    failed_rows = models.PositiveIntegerField(default=0, verbose_name='Failed Rows')
    errors = models.JSONField(default=list, blank=True, verbose_name='Errors')
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='csv_imports',
        verbose_name='Imported By',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'CSV Import'
        verbose_name_plural = 'CSV Imports'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.file_name} ({self.status})'


class Registro(models.Model):
    """A record imported from CSV, representing an email in a Unidade/Setor hierarchy."""

    email = models.EmailField(verbose_name='Email')
    unidade = models.ForeignKey(
        Unidade,
        on_delete=models.CASCADE,
        related_name='registros',
        verbose_name='Unidade',
    )
    setor = models.ForeignKey(
        Setor,
        on_delete=models.CASCADE,
        related_name='registros',
        verbose_name='Setor',
    )
    csv_import = models.ForeignKey(
        CSVImport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros',
        verbose_name='CSV Import',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro'
        verbose_name_plural = 'Registros'
        ordering = ['unidade__name', 'setor__name', 'email']
        unique_together = ('email', 'unidade', 'setor')

    def __str__(self) -> str:
        return f'{self.email} | {self.unidade.name} / {self.setor.name}'


class LeaderPermission(models.Model):
    """
    Defines which Unidade/Setor combinations a LEADER user can access.

    If setor is NULL the leader can see all setores within that unidade.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leader_permissions',
        verbose_name='User',
    )
    unidade = models.ForeignKey(
        Unidade,
        on_delete=models.CASCADE,
        related_name='leader_permissions',
        verbose_name='Unidade',
    )
    setor = models.ForeignKey(
        Setor,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leader_permissions',
        verbose_name='Setor',
    )

    class Meta:
        verbose_name = 'Leader Permission'
        verbose_name_plural = 'Leader Permissions'
        unique_together = ('user', 'unidade', 'setor')

    def __str__(self) -> str:
        setor_str = self.setor.name if self.setor else '(all)'
        return f'{self.user.email} → {self.unidade.name} / {setor_str}'
