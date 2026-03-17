"""Views for organizational hierarchy and CSV import."""

from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import UserRole
from apps.users.permissions import IsRH, IsRHOrLeader

from .models import CSVImport, LeaderPermission, Registro, Setor, Unidade
from .serializers import (
    CSVImportSerializer,
    LeaderPermissionSerializer,
    LeaderPermissionWriteSerializer,
    RegistroSerializer,
    SetorSerializer,
    UnidadeSerializer,
)
from .services import CSVImportService


# ── Unidade ───────────────────────────────────────────────────────────────────

class UnidadeListCreateView(generics.ListCreateAPIView):
    """List all Unidades or create a new one (RH/GLOBAL_ADMIN only for writes)."""

    serializer_class = UnidadeSerializer
    permission_classes = (IsRHOrLeader,)

    def get_queryset(self):
        user = self.request.user
        if user.role in (UserRole.RH, UserRole.GLOBAL_ADMIN):
            return Unidade.objects.prefetch_related('setores').all()

        # LEADER: only unidades with explicit permission
        allowed_ids = LeaderPermission.objects.filter(user=user).values_list(
            'unidade_id', flat=True
        ).distinct()
        return Unidade.objects.prefetch_related('setores').filter(pk__in=allowed_ids)

    def perform_create(self, serializer):
        # Only RH/GLOBAL_ADMIN can create (enforced by IsRH in POST check)
        if self.request.user.role not in (UserRole.RH, UserRole.GLOBAL_ADMIN):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only RH or GLOBAL_ADMIN can create Unidades.')
        serializer.save()


class UnidadeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UnidadeSerializer
    permission_classes = (IsRH,)
    queryset = Unidade.objects.all()


# ── Setor ─────────────────────────────────────────────────────────────────────

class SetorListCreateView(generics.ListCreateAPIView):
    """List Setores (filtered by user permissions) or create (RH/GLOBAL_ADMIN)."""

    serializer_class = SetorSerializer
    permission_classes = (IsRHOrLeader,)

    def get_queryset(self):
        user = self.request.user
        qs = Setor.objects.select_related('unidade').all()

        unidade_id = self.request.query_params.get('unidade')
        if unidade_id:
            qs = qs.filter(unidade_id=unidade_id)

        if user.role in (UserRole.RH, UserRole.GLOBAL_ADMIN):
            return qs

        # LEADER: restrict by permissions
        from django.db.models import Q
        perms = LeaderPermission.objects.filter(user=user)
        # Build query: either permission has setor set (exact match) or setor is null (all setores)
        unidade_all = perms.filter(setor__isnull=True).values_list('unidade_id', flat=True)
        setor_exact = perms.filter(setor__isnull=False).values_list('setor_id', flat=True)
        return qs.filter(Q(unidade_id__in=unidade_all) | Q(pk__in=setor_exact))

    def perform_create(self, serializer):
        if self.request.user.role not in (UserRole.RH, UserRole.GLOBAL_ADMIN):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only RH or GLOBAL_ADMIN can create Setores.')
        serializer.save()


class SetorDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SetorSerializer
    permission_classes = (IsRH,)
    queryset = Setor.objects.select_related('unidade').all()


# ── Registro ──────────────────────────────────────────────────────────────────

class RegistroListView(generics.ListAPIView):
    """List Registros, filtered by tenant and user role."""

    serializer_class = RegistroSerializer
    permission_classes = (IsRHOrLeader,)

    def get_queryset(self):
        user = self.request.user
        qs = Registro.objects.select_related('unidade', 'setor').all()

        unidade_id = self.request.query_params.get('unidade')
        setor_id = self.request.query_params.get('setor')
        if unidade_id:
            qs = qs.filter(unidade_id=unidade_id)
        if setor_id:
            qs = qs.filter(setor_id=setor_id)

        if user.role in (UserRole.RH, UserRole.GLOBAL_ADMIN):
            return qs

        # LEADER: apply permission filter
        from django.db.models import Q
        perms = LeaderPermission.objects.filter(user=user)
        unidade_all = perms.filter(setor__isnull=True).values_list('unidade_id', flat=True)
        setor_exact = perms.filter(setor__isnull=False).values_list('setor_id', flat=True)
        return qs.filter(Q(unidade_id__in=unidade_all) | Q(setor_id__in=setor_exact))


# ── CSV Import ────────────────────────────────────────────────────────────────

class CSVImportListView(generics.ListAPIView):
    """List all CSV import records for the current tenant (RH only)."""

    serializer_class = CSVImportSerializer
    permission_classes = (IsRH,)

    def get_queryset(self):
        return CSVImport.objects.all()


class CSVImportUploadView(APIView):
    """Upload a CSV file and trigger the import pipeline."""

    permission_classes = (IsRH,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request: Request) -> Response:
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        if not file_obj.name.lower().endswith('.csv'):
            return Response(
                {'detail': 'Only CSV files are accepted.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = CSVImportService(
            file_name=file_obj.name,
            file_content=file_obj.read(),
            imported_by=request.user,
        )
        csv_import = service.process()
        serializer = CSVImportSerializer(csv_import)

        http_status = (
            status.HTTP_201_CREATED
            if csv_import.status == CSVImport.Status.COMPLETED
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return Response(serializer.data, status=http_status)


# ── Leader Permissions ────────────────────────────────────────────────────────

class LeaderPermissionView(APIView):
    """
    GET  /api/organizational/permissions/<user_pk>/  – list permissions
    PUT  /api/organizational/permissions/<user_pk>/  – replace all permissions
    """

    permission_classes = (IsRH,)

    def get(self, request: Request, user_pk: int) -> Response:
        perms = LeaderPermission.objects.filter(user_id=user_pk).select_related('unidade', 'setor')
        serializer = LeaderPermissionSerializer(perms, many=True)
        return Response(serializer.data)

    def put(self, request: Request, user_pk: int) -> Response:
        from apps.users.models import User, UserRole

        try:
            target_user = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if target_user.role != UserRole.LEADER:
            return Response(
                {'detail': 'Permissions can only be set for LEADER users.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        write_serializer = LeaderPermissionWriteSerializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        permissions = write_serializer.validated_data['permissions']

        # Replace all permissions atomically
        from django.db import transaction
        with transaction.atomic():
            LeaderPermission.objects.filter(user_id=user_pk).delete()
            for perm in permissions:
                LeaderPermission.objects.create(
                    user_id=user_pk,
                    unidade=perm['unidade'],
                    setor=perm.get('setor'),
                )

        perms = LeaderPermission.objects.filter(user_id=user_pk).select_related('unidade', 'setor')
        return Response(LeaderPermissionSerializer(perms, many=True).data)
