"""Business logic services for the campaigns domain."""

from __future__ import annotations

import hashlib
import hmac
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    Campaign,
    DimensionScore,
    HSEDimension,
    HSEQuestion,
    SurveyAnswer,
    SurveyInvite,
    SurveyResponse,
)

logger = logging.getLogger(__name__)


# ── Email hashing ──────────────────────────────────────────────────────────────

class EmailHashService:
    """
    Provides LGPD-compliant deterministic hashing for email addresses.

    Uses HMAC-SHA256 with the Django SECRET_KEY.  The hash is:
      • deterministic – same email always produces the same digest,
        enabling uniqueness checks without storing the real address.
      • irreversible  – the raw email cannot be recovered from the hash.
      • unique per deployment – the secret key prevents rainbow-table attacks.
    """

    @staticmethod
    def hash(email: str) -> str:
        """Return a 64-char hex HMAC-SHA256 digest of *email*."""
        key = settings.SECRET_KEY.encode('utf-8')
        msg = email.strip().lower().encode('utf-8')
        return hmac.new(key, msg, hashlib.sha256).hexdigest()


# ── Score calculation ──────────────────────────────────────────────────────────

_RISK_THRESHOLDS: list[tuple[float, str]] = [
    (1.0, DimensionScore.RiskLevel.ACCEPTABLE),
    (2.5, DimensionScore.RiskLevel.MODERATE),
    (3.5, DimensionScore.RiskLevel.IMPORTANT),
    (4.01, DimensionScore.RiskLevel.CRITICAL),
]


def _risk_level(risk_score: Decimal) -> str:
    v = float(risk_score)
    for threshold, level in _RISK_THRESHOLDS:
        if v < threshold:
            return level
    return DimensionScore.RiskLevel.CRITICAL


class ScoreCalculationService:
    """Computes dimension scores and populates DimensionScore rows."""

    @staticmethod
    def compute_risk_score(
        score: Decimal,
        dimension_type: str,
    ) -> Decimal:
        """
        Convert a raw dimension score (0–4) into a risk score (0–4).

        Negative dims (Demandas, Relacionamentos): high score → high risk.
        Positive dims: low score → high risk, so risk = 4 – score.
        """
        if dimension_type == HSEDimension.DimensionType.NEGATIVE:
            return score
        return Decimal('4.00') - score

    @classmethod
    def calculate_and_store(cls, response: SurveyResponse) -> list[DimensionScore]:
        """
        Calculate a DimensionScore for every dimension based on *response* answers,
        then bulk-create them.  Returns the created DimensionScore instances.
        """
        invite = response.invite

        # Group answers by dimension
        answers = (
            SurveyAnswer.objects.filter(response=response)
            .select_related('question__dimension')
        )
        dimension_answers: dict[int, list[int]] = {}
        dimension_obj: dict[int, HSEDimension] = {}
        for ans in answers:
            dim = ans.question.dimension
            dimension_answers.setdefault(dim.pk, []).append(ans.value)
            dimension_obj[dim.pk] = dim

        scores: list[DimensionScore] = []
        for dim_id, values in dimension_answers.items():
            dim = dimension_obj[dim_id]
            raw = Decimal(sum(values)) / Decimal(len(values))
            raw = raw.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            risk = cls.compute_risk_score(raw, dim.dimension_type)
            risk = risk.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            level = _risk_level(risk)
            scores.append(
                DimensionScore(
                    response=response,
                    campaign=response.campaign,
                    dimension=dim,
                    score=raw,
                    risk_score=risk,
                    risk_level=level,
                    unidade_id=invite.unidade_id,
                    setor_id=invite.setor_id,
                    gender=response.gender,
                    age_range=response.age_range,
                )
            )

        DimensionScore.objects.bulk_create(scores)
        return scores


# ── Campaign service ───────────────────────────────────────────────────────────

class CampaignService:
    """CRUD operations for Campaign objects."""

    @staticmethod
    def create(name: str, description: str, created_by) -> Campaign:
        return Campaign.objects.create(
            name=name,
            description=description,
            created_by=created_by,
        )

    @staticmethod
    def activate(campaign: Campaign) -> Campaign:
        campaign.status = Campaign.Status.ACTIVE
        campaign.save(update_fields=['status', 'updated_at'])
        return campaign

    @staticmethod
    def close(campaign: Campaign) -> Campaign:
        campaign.status = Campaign.Status.CLOSED
        campaign.save(update_fields=['status', 'updated_at'])
        return campaign


# ── Invite service ─────────────────────────────────────────────────────────────

class InviteService:
    """Creates and sends survey invites for a campaign."""

    @staticmethod
    def create_invites_from_registros(campaign: Campaign, registros) -> list[SurveyInvite]:
        """
        Create SurveyInvite entries from an iterable of Registro objects.
        Skips duplicates (same campaign + email_hash) silently.
        """
        created: list[SurveyInvite] = []
        for registro in registros:
            email_hash = EmailHashService.hash(registro.email)
            invite, is_new = SurveyInvite.objects.get_or_create(
                campaign=campaign,
                email_hash=email_hash,
                defaults={
                    'registro_id': registro.pk,
                    'unidade_id': registro.unidade_id,
                    'setor_id': registro.setor_id,
                },
            )
            if is_new:
                created.append(invite)
        return created

    @staticmethod
    def send_invite(invite: SurveyInvite) -> None:
        """Enqueue an async Celery task to send the survey email."""
        from .tasks import send_survey_email  # avoid circular import at module level

        if invite.is_answered:
            logger.warning('Skipping already-answered invite %s', invite.pk)
            return

        send_survey_email.delay(invite.pk)

    @staticmethod
    def send_bulk(invite_ids: list[int]) -> int:
        """Send multiple invites by primary key. Returns count enqueued."""
        from .tasks import send_survey_email

        invites = SurveyInvite.objects.filter(
            pk__in=invite_ids,
            response_status=SurveyInvite.ResponseStatus.PENDING,
        )
        count = 0
        for invite in invites:
            send_survey_email.delay(invite.pk)
            count += 1
        return count


# ── Survey submission service ──────────────────────────────────────────────────

class SurveySubmissionService:
    """Validates a magic-link token, records answers and computes scores."""

    @staticmethod
    def get_invite_by_token(token: str) -> SurveyInvite | None:
        try:
            return SurveyInvite.objects.select_related('campaign').get(token=token)
        except SurveyInvite.DoesNotExist:
            return None

    @classmethod
    @transaction.atomic
    def submit(
        cls,
        token: str,
        consent: bool,
        gender: str | None,
        age_range: str | None,
        answers: dict[int, int],  # {question_id: value}
    ) -> SurveyResponse:
        """
        Validate token, persist SurveyResponse + SurveyAnswer rows, compute scores.
        Raises ValueError on invalid/used tokens or missing consent.
        """
        invite = cls.get_invite_by_token(token)
        if invite is None:
            raise ValueError('Token inválido.')
        if invite.is_answered:
            raise ValueError('Este link já foi utilizado.')
        if invite.campaign.status != Campaign.Status.ACTIVE:
            raise ValueError('Esta campanha não está ativa.')
        if not consent:
            raise ValueError('O consentimento é obrigatório para participar.')

        response = SurveyResponse.objects.create(
            campaign=invite.campaign,
            invite=invite,
            gender=gender or None,
            age_range=age_range or None,
            consent_given=True,
        )

        # Persist answers
        questions = {q.pk: q for q in HSEQuestion.objects.all()}
        answer_objs: list[SurveyAnswer] = []
        for q_id, value in answers.items():
            if q_id not in questions:
                continue
            if value not in range(5):
                raise ValueError(f'Valor inválido {value} para pergunta {q_id}.')
            answer_objs.append(
                SurveyAnswer(response=response, question_id=q_id, value=value)
            )
        SurveyAnswer.objects.bulk_create(answer_objs)

        # Mark invite as answered
        invite.response_status = SurveyInvite.ResponseStatus.ANSWERED
        invite.save(update_fields=['response_status'])

        # Enqueue async score computation via Celery (never block the request)
        from .tasks import compute_dimension_scores
        compute_dimension_scores.delay(response.pk)

        return response


# ── Dashboard service ──────────────────────────────────────────────────────────

class DashboardService:
    """Aggregates DimensionScore data for dashboard rendering."""

    @staticmethod
    def get_summary(campaign: Campaign) -> dict[str, Any]:
        from django.db.models import Avg, Count, Q

        total_invites = campaign.invites.count()
        total_answered = campaign.invites.filter(
            response_status=SurveyInvite.ResponseStatus.ANSWERED
        ).count()
        adhesion_rate = (
            round(total_answered / total_invites * 100, 1) if total_invites else 0.0
        )

        # Average risk scores per dimension across the campaign
        dim_scores = (
            DimensionScore.objects
            .filter(campaign=campaign)
            .values('dimension__id', 'dimension__name', 'dimension__dimension_type', 'dimension__order')
            .annotate(avg_score=Avg('score'), avg_risk=Avg('risk_score'))
            .order_by('dimension__order')
        )

        # IGRP = mean of all avg_risk values
        igrp = 0.0
        if dim_scores:
            igrp = round(sum(float(d['avg_risk']) for d in dim_scores) / len(dim_scores), 2)

        # Risk level distribution
        risk_counts = (
            DimensionScore.objects
            .filter(campaign=campaign)
            .values('risk_level')
            .annotate(count=Count('id'))
        )
        risk_distribution = {r['risk_level']: r['count'] for r in risk_counts}

        high_risk_count = (
            risk_distribution.get(DimensionScore.RiskLevel.IMPORTANT, 0)
            + risk_distribution.get(DimensionScore.RiskLevel.CRITICAL, 0)
        )
        total_scores = sum(risk_distribution.values())
        high_risk_pct = round(high_risk_count / total_scores * 100, 1) if total_scores else 0.0

        return {
            'total_invites': total_invites,
            'total_answered': total_answered,
            'adhesion_rate': adhesion_rate,
            'igrp': igrp,
            'high_risk_pct': high_risk_pct,
            'dimension_scores': list(dim_scores),
            'risk_distribution': risk_distribution,
        }

    @staticmethod
    def get_gender_scores(campaign: Campaign) -> list[dict]:
        from django.db.models import Avg
        return list(
            DimensionScore.objects
            .filter(campaign=campaign)
            .exclude(gender__isnull=True)
            .values('gender', 'dimension__name', 'dimension__order')
            .annotate(avg_score=Avg('score'))
            .order_by('dimension__order', 'gender')
        )

    @staticmethod
    def get_age_range_scores(campaign: Campaign) -> list[dict]:
        from django.db.models import Avg
        return list(
            DimensionScore.objects
            .filter(campaign=campaign)
            .exclude(age_range__isnull=True)
            .values('age_range', 'dimension__name', 'dimension__order')
            .annotate(avg_score=Avg('score'))
            .order_by('dimension__order', 'age_range')
        )

    @staticmethod
    def get_sector_heatmap(campaign: Campaign) -> list[dict]:
        from django.db.models import Avg
        return list(
            DimensionScore.objects
            .filter(campaign=campaign)
            .exclude(setor_id__isnull=True)
            .values('setor_id', 'dimension__name', 'dimension__order')
            .annotate(avg_risk=Avg('risk_score'))
            .order_by('setor_id', 'dimension__order')
        )

    @staticmethod
    def get_critical_sectors(campaign: Campaign) -> list[dict]:
        from django.db.models import Avg, Count
        return list(
            DimensionScore.objects
            .filter(campaign=campaign, risk_level__in=[
                DimensionScore.RiskLevel.IMPORTANT,
                DimensionScore.RiskLevel.CRITICAL,
            ])
            .exclude(setor_id__isnull=True)
            .values('setor_id')
            .annotate(
                high_risk_count=Count('id'),
                avg_risk=Avg('risk_score'),
            )
            .order_by('-avg_risk')[:10]
        )

    @staticmethod
    def get_demographic_groups(campaign: Campaign) -> dict[str, list[dict]]:
        from django.db.models import Avg
        gender_groups = list(
            DimensionScore.objects
            .filter(campaign=campaign)
            .exclude(gender__isnull=True)
            .values('gender')
            .annotate(avg_risk=Avg('risk_score'))
            .order_by('-avg_risk')
        )
        age_groups = list(
            DimensionScore.objects
            .filter(campaign=campaign)
            .exclude(age_range__isnull=True)
            .values('age_range')
            .annotate(avg_risk=Avg('risk_score'))
            .order_by('-avg_risk')
        )
        return {'by_gender': gender_groups, 'by_age_range': age_groups}
