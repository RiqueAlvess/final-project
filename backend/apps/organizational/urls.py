"""URL patterns for organizational module."""

from django.urls import path

from .views import (
    CSVImportListView,
    CSVImportUploadView,
    LeaderPermissionView,
    RegistroListView,
    SetorDetailView,
    SetorListCreateView,
    UnidadeDetailView,
    UnidadeListCreateView,
)

app_name = 'organizational'

urlpatterns = [
    # Unidades
    path('unidades/', UnidadeListCreateView.as_view(), name='unidade-list-create'),
    path('unidades/<int:pk>/', UnidadeDetailView.as_view(), name='unidade-detail'),

    # Setores
    path('setores/', SetorListCreateView.as_view(), name='setor-list-create'),
    path('setores/<int:pk>/', SetorDetailView.as_view(), name='setor-detail'),

    # Registros
    path('registros/', RegistroListView.as_view(), name='registro-list'),

    # CSV Import
    path('csv-imports/', CSVImportListView.as_view(), name='csv-import-list'),
    path('csv-imports/upload/', CSVImportUploadView.as_view(), name='csv-import-upload'),

    # Leader permissions
    path('permissions/<int:user_pk>/', LeaderPermissionView.as_view(), name='leader-permissions'),
]
