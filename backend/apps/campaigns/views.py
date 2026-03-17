"""API views for campaigns, invites, survey submission and dashboard."""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import UserRole
from apps.users.permissions import IsRH, IsRHOrLeader

from .models import Campaign, HSEDimension, SurveyInvite
from .serializers import (
    BulkSendSerializer,
    CampaignSerializer,
    CampaignWriteSerializer,
    DashboardSummarySerializer,
    HSEDimensionSerializer,
    SurveyInviteSerializer,
    SurveySubmitSerializer,
)
from .services import (
    CampaignService,
    InviteService,
    SurveySubmissionService,
)
from . import selectors


# ── Campaigns ──────────────────────────────────────────────────────────────────

class CampaignListCreateView(generics.ListCreateAPIView):
    """List all campaigns or create a new one (RH only)."""

    permission_classes = (IsRH,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CampaignWriteSerializer
        return CampaignSerializer

    def get_queryset(self):
        return Campaign.objects.prefetch_related('invites').all()

    def perform_create(self, serializer):
        CampaignService.create(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            created_by=self.request.user,
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = CampaignWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        campaign = CampaignService.create(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            created_by=request.user,
        )
        return Response(CampaignSerializer(campaign).data, status=status.HTTP_201_CREATED)


class CampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a campaign (RH only)."""

    permission_classes = (IsRH,)
    queryset = Campaign.objects.all()

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CampaignWriteSerializer
        return CampaignSerializer


class CampaignActivateView(APIView):
    """Activate a campaign (sets status to ACTIVE)."""

    permission_classes = (IsRH,)

    def post(self, request: Request, pk: int) -> Response:
        try:
            campaign = Campaign.objects.get(pk=pk)
        except Campaign.DoesNotExist:
            return Response({'detail': 'Campanha não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        campaign = CampaignService.activate(campaign)
        return Response(CampaignSerializer(campaign).data)


class CampaignCloseView(APIView):
    """Close a campaign."""

    permission_classes = (IsRH,)

    def post(self, request: Request, pk: int) -> Response:
        try:
            campaign = Campaign.objects.get(pk=pk)
        except Campaign.DoesNotExist:
            return Response({'detail': 'Campanha não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        campaign = CampaignService.close(campaign)
        return Response(CampaignSerializer(campaign).data)


# ── Invites ────────────────────────────────────────────────────────────────────

class InviteListView(generics.ListAPIView):
    """List all invites for a campaign (RH only)."""

    permission_classes = (IsRH,)
    serializer_class = SurveyInviteSerializer

    def get_queryset(self):
        campaign_pk = self.kwargs['campaign_pk']
        return SurveyInvite.objects.filter(campaign_id=campaign_pk).order_by('-created_at')


class CreateInvitesFromRegistrosView(APIView):
    """
    POST  /api/campaigns/<pk>/invites/import/
    Import invites from all Registros for this tenant into the campaign.
    """

    permission_classes = (IsRH,)

    def post(self, request: Request, pk: int) -> Response:
        from apps.organizational.models import Registro

        try:
            campaign = Campaign.objects.get(pk=pk)
        except Campaign.DoesNotExist:
            return Response({'detail': 'Campanha não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        registros = Registro.objects.all()
        if not registros.exists():
            return Response(
                {'detail': 'Nenhum registro encontrado. Importe colaboradores via CSV primeiro.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = InviteService.create_invites_from_registros(campaign, registros)
        return Response(
            {'created': len(created), 'total': campaign.invites.count()},
            status=status.HTTP_201_CREATED,
        )


class BulkSendInvitesView(APIView):
    """
    POST  /api/campaigns/<pk>/invites/send/
    Enqueue email delivery for a list of invite IDs.
    """

    permission_classes = (IsRH,)

    def post(self, request: Request, pk: int) -> Response:
        serializer = BulkSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invite_ids = serializer.validated_data['invite_ids']
        # Verify all invites belong to this campaign
        valid = SurveyInvite.objects.filter(
            pk__in=invite_ids, campaign_id=pk
        ).values_list('pk', flat=True)

        count = InviteService.send_bulk(list(valid))
        return Response({'enqueued': count})


# ── Public survey (no auth) ────────────────────────────────────────────────────

class SurveyTokenValidateView(APIView):
    """
    GET  /api/survey/<token>/
    Returns campaign info + all HSE questions if token is valid and unused.
    """

    permission_classes = (AllowAny,)
    authentication_classes = ()

    def get(self, request: Request, token: str) -> Response:
        invite = SurveySubmissionService.get_invite_by_token(token)
        if invite is None:
            return Response(
                {'detail': 'Link inválido.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if invite.is_answered:
            return Response(
                {'detail': 'Este link já foi utilizado.', 'answered': True},
                status=status.HTTP_410_GONE,
            )
        if invite.campaign.status != Campaign.Status.ACTIVE:
            return Response(
                {'detail': 'Esta campanha não está ativa.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        dimensions = HSEDimension.objects.prefetch_related('questions').order_by('order')
        return Response({
            'campaign': {
                'id': invite.campaign.pk,
                'name': invite.campaign.name,
                'description': invite.campaign.description,
            },
            'dimensions': HSEDimensionSerializer(dimensions, many=True).data,
        })


class SurveySubmitView(APIView):
    """
    POST  /api/survey/<token>/submit/
    Validates and persists a complete survey submission.
    """

    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request: Request, token: str) -> Response:
        serializer = SurveySubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        answers_raw = {
            a['question_id']: a['value']
            for a in serializer.validated_data['answers']
        }

        try:
            SurveySubmissionService.submit(
                token=token,
                consent=serializer.validated_data['consent'],
                gender=serializer.validated_data.get('gender') or None,
                age_range=serializer.validated_data.get('age_range') or None,
                answers=answers_raw,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': 'Pesquisa enviada com sucesso. Obrigado!'})


# ── Dashboard ──────────────────────────────────────────────────────────────────

def _parse_int_list(raw: str | None) -> list[int]:
    """Parse a comma-separated string of ints from a query param, e.g. '1,2,3'."""
    if not raw:
        return []
    result = []
    for part in raw.split(','):
        part = part.strip()
        if part.isdigit():
            result.append(int(part))
    return result


def _enforce_leader_filters(
    user,
    requested_unidade_ids: list[int],
    requested_setor_ids: list[int],
) -> tuple[list[int] | None, list[int] | None]:
    """
    For LEADER users, intersect the requested filters with their granted permissions.
    Returns (allowed_unidade_ids, allowed_setor_ids).
    For RH/GLOBAL_ADMIN returns the requested lists unchanged (None means no filter).
    """
    if user.role in (UserRole.RH, UserRole.GLOBAL_ADMIN):
        return requested_unidade_ids or None, requested_setor_ids or None

    from apps.organizational.models import LeaderPermission, Setor
    from django.db.models import Q

    perms = LeaderPermission.objects.filter(user=user)
    unidade_all = set(perms.filter(setor__isnull=True).values_list('unidade_id', flat=True))
    setor_exact = set(perms.filter(setor__isnull=False).values_list('setor_id', flat=True))

    # Build full allowed setor set for leader
    all_allowed_setor_ids = set(
        Setor.objects.filter(unidade_id__in=unidade_all).values_list('pk', flat=True)
    ) | setor_exact
    all_allowed_unidade_ids = unidade_all | set(
        perms.filter(setor__isnull=False).values_list('unidade_id', flat=True)
    )

    if requested_unidade_ids:
        allowed_u = [u for u in requested_unidade_ids if u in all_allowed_unidade_ids]
    else:
        allowed_u = list(all_allowed_unidade_ids)

    if requested_setor_ids:
        allowed_s = [s for s in requested_setor_ids if s in all_allowed_setor_ids]
    else:
        # When no setor filter requested, use all allowed setores (limit to selected unidades)
        if allowed_u:
            allowed_s = list(
                Setor.objects.filter(unidade_id__in=allowed_u)
                .filter(pk__in=all_allowed_setor_ids)
                .values_list('pk', flat=True)
            )
        else:
            allowed_s = list(all_allowed_setor_ids)

    return allowed_u or None, allowed_s or None


class CampaignDashboardView(APIView):
    """
    GET  /api/campaigns/<pk>/dashboard/

    Accepts optional query params:
      - unidade_ids  comma-separated list of Unidade PKs to filter by
      - setor_ids    comma-separated list of Setor PKs to filter by

    For LEADER users the backend enforces that only their permitted
    unidades/setores are used regardless of what the request sends.
    All data is read from the pre-computed DimensionScore star-schema table
    via selectors — no calculation happens at request time.
    """

    permission_classes = (IsRHOrLeader,)

    def get(self, request: Request, pk: int) -> Response:
        try:
            campaign = Campaign.objects.get(pk=pk)
        except Campaign.DoesNotExist:
            return Response({'detail': 'Campanha não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        # Parse requested filters from query params
        req_unidade_ids = _parse_int_list(request.query_params.get('unidade_ids'))
        req_setor_ids = _parse_int_list(request.query_params.get('setor_ids'))

        # Enforce role-based access: LEADER cannot see data outside their permissions
        unidade_ids, setor_ids = _enforce_leader_filters(
            request.user, req_unidade_ids, req_setor_ids
        )

        return Response({
            'campaign': CampaignSerializer(campaign).data,
            'summary': selectors.get_campaign_summary(campaign, unidade_ids, setor_ids),
            'gender_scores': selectors.get_scores_por_genero(campaign, unidade_ids, setor_ids),
            'age_range_scores': selectors.get_scores_por_faixa_etaria(campaign, unidade_ids, setor_ids),
            'sector_heatmap': selectors.get_heatmap_data(campaign, unidade_ids, setor_ids),
            'critical_sectors': selectors.get_top_setores_criticos(campaign, unidade_ids, setor_ids),
            'demographic_groups': selectors.get_grupos_criticos(campaign, unidade_ids, setor_ids),
        })


class DashboardFiltersView(APIView):
    """
    GET  /api/campaigns/<pk>/dashboard/filters/

    Returns the unidades and setores available for the current user to filter by.
    RH sees all that appear in the campaign data; LEADER sees only permitted ones.
    """

    permission_classes = (IsRHOrLeader,)

    def get(self, request: Request, pk: int) -> Response:
        try:
            campaign = Campaign.objects.get(pk=pk)
        except Campaign.DoesNotExist:
            return Response({'detail': 'Campanha não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        filters = selectors.get_filtros_disponiveis(campaign, request.user)
        return Response(filters)
