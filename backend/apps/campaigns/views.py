"""API views for campaigns, invites, survey submission and dashboard."""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsRH

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
    DashboardService,
    InviteService,
    SurveySubmissionService,
)


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

class CampaignDashboardView(APIView):
    """
    GET  /api/campaigns/<pk>/dashboard/
    Returns all aggregated analytics for a campaign.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, pk: int) -> Response:
        try:
            campaign = Campaign.objects.get(pk=pk)
        except Campaign.DoesNotExist:
            return Response({'detail': 'Campanha não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        summary = DashboardService.get_summary(campaign)
        gender_scores = DashboardService.get_gender_scores(campaign)
        age_scores = DashboardService.get_age_range_scores(campaign)
        heatmap = DashboardService.get_sector_heatmap(campaign)
        critical_sectors = DashboardService.get_critical_sectors(campaign)
        demographic = DashboardService.get_demographic_groups(campaign)

        return Response({
            'campaign': CampaignSerializer(campaign).data,
            'summary': summary,
            'gender_scores': gender_scores,
            'age_range_scores': age_scores,
            'sector_heatmap': heatmap,
            'critical_sectors': critical_sectors,
            'demographic_groups': demographic,
        })
