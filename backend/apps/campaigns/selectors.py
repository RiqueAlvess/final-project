"""
Read-only selectors for dashboard analytics.

All selectors operate exclusively on the DimensionScore star-schema fact table.
No metric is computed at request time — all values were pre-computed and stored
by the async Celery pipeline when survey responses were submitted.

Every public selector accepts optional ``unidade_ids`` and ``setor_ids``
parameters so that callers (views) can apply organisational-unit filters
without any filtering logic leaking into views or serializers.
"""

from __future__ import annotations

from typing import Any

from django.db.models import Avg, Count, QuerySet

from .models import Campaign, DimensionScore, SurveyInvite


# ── helpers ──────────────────────────────────────────────────────────────────

def _apply_org_filters(
    qs: QuerySet,
    unidade_ids: list[int] | None,
    setor_ids: list[int] | None,
) -> QuerySet:
    """
    Apply unidade / setor filters to a DimensionScore queryset.

    Rules:
    - If both lists are empty / None, the queryset is returned unchanged.
    - Providing unidade_ids filters all rows to those unidades.
    - Providing setor_ids further narrows to those setores **inside** the
      already-selected unidades.  If unidade_ids is absent, only setor_ids
      is applied.
    """
    if unidade_ids:
        qs = qs.filter(unidade_id__in=unidade_ids)
    if setor_ids:
        qs = qs.filter(setor_id__in=setor_ids)
    return qs


def _base_qs(
    campaign: Campaign,
    unidade_ids: list[int] | None = None,
    setor_ids: list[int] | None = None,
) -> QuerySet:
    qs = DimensionScore.objects.filter(campaign=campaign)
    return _apply_org_filters(qs, unidade_ids, setor_ids)


# ── public selectors ──────────────────────────────────────────────────────────

def get_campaign_summary(
    campaign: Campaign,
    unidade_ids: list[int] | None = None,
    setor_ids: list[int] | None = None,
) -> dict[str, Any]:
    """
    Returns summary KPIs: adhesion rate, IGRP, risk distribution.

    Invite counts respect the same unidade/setor filters so that
    the adhesion rate is scoped to the filtered population.
    """
    invite_qs = SurveyInvite.objects.filter(campaign=campaign)
    if unidade_ids:
        invite_qs = invite_qs.filter(unidade_id__in=unidade_ids)
    if setor_ids:
        invite_qs = invite_qs.filter(setor_id__in=setor_ids)

    total_invites = invite_qs.count()
    total_answered = invite_qs.filter(
        response_status=SurveyInvite.ResponseStatus.ANSWERED
    ).count()
    adhesion_rate = (
        round(total_answered / total_invites * 100, 1) if total_invites else 0.0
    )

    qs = _base_qs(campaign, unidade_ids, setor_ids)

    dim_scores = list(
        qs.values(
            'dimension__id',
            'dimension__name',
            'dimension__dimension_type',
            'dimension__order',
        )
        .annotate(avg_score=Avg('score'), avg_risk=Avg('risk_score'))
        .order_by('dimension__order')
    )

    igrp = 0.0
    if dim_scores:
        igrp = round(
            sum(float(d['avg_risk']) for d in dim_scores) / len(dim_scores), 2
        )

    risk_counts = (
        qs.values('risk_level').annotate(count=Count('id'))
    )
    risk_distribution = {r['risk_level']: r['count'] for r in risk_counts}

    high_risk_count = (
        risk_distribution.get(DimensionScore.RiskLevel.IMPORTANT, 0)
        + risk_distribution.get(DimensionScore.RiskLevel.CRITICAL, 0)
    )
    total_scores = sum(risk_distribution.values())
    high_risk_pct = (
        round(high_risk_count / total_scores * 100, 1) if total_scores else 0.0
    )

    return {
        'total_invites': total_invites,
        'total_answered': total_answered,
        'adhesion_rate': adhesion_rate,
        'igrp': igrp,
        'high_risk_pct': high_risk_pct,
        'dimension_scores': dim_scores,
        'risk_distribution': risk_distribution,
    }


def get_dimensoes_scores(
    campaign: Campaign,
    unidade_ids: list[int] | None = None,
    setor_ids: list[int] | None = None,
) -> list[dict]:
    """Average score and risk score per HSE dimension."""
    return list(
        _base_qs(campaign, unidade_ids, setor_ids)
        .values('dimension__id', 'dimension__name', 'dimension__order')
        .annotate(avg_score=Avg('score'), avg_risk=Avg('risk_score'))
        .order_by('dimension__order')
    )


def get_scores_por_genero(
    campaign: Campaign,
    unidade_ids: list[int] | None = None,
    setor_ids: list[int] | None = None,
) -> list[dict]:
    """Average score per dimension broken down by gender."""
    return list(
        _base_qs(campaign, unidade_ids, setor_ids)
        .exclude(gender__isnull=True)
        .values('gender', 'dimension__name', 'dimension__order')
        .annotate(avg_score=Avg('score'))
        .order_by('dimension__order', 'gender')
    )


def get_scores_por_faixa_etaria(
    campaign: Campaign,
    unidade_ids: list[int] | None = None,
    setor_ids: list[int] | None = None,
) -> list[dict]:
    """Average score per dimension broken down by age range."""
    return list(
        _base_qs(campaign, unidade_ids, setor_ids)
        .exclude(age_range__isnull=True)
        .values('age_range', 'dimension__name', 'dimension__order')
        .annotate(avg_score=Avg('score'))
        .order_by('dimension__order', 'age_range')
    )


def get_heatmap_data(
    campaign: Campaign,
    unidade_ids: list[int] | None = None,
    setor_ids: list[int] | None = None,
) -> list[dict]:
    """Average risk score per setor × dimension cell (heatmap)."""
    return list(
        _base_qs(campaign, unidade_ids, setor_ids)
        .exclude(setor_id__isnull=True)
        .values('setor_id', 'dimension__name', 'dimension__order')
        .annotate(avg_risk=Avg('risk_score'))
        .order_by('setor_id', 'dimension__order')
    )


def get_top_setores_criticos(
    campaign: Campaign,
    unidade_ids: list[int] | None = None,
    setor_ids: list[int] | None = None,
    limit: int = 10,
) -> list[dict]:
    """Top sectors ranked by average risk (only IMPORTANT/CRITICAL rows counted)."""
    return list(
        _base_qs(campaign, unidade_ids, setor_ids)
        .filter(
            risk_level__in=[
                DimensionScore.RiskLevel.IMPORTANT,
                DimensionScore.RiskLevel.CRITICAL,
            ]
        )
        .exclude(setor_id__isnull=True)
        .values('setor_id')
        .annotate(
            high_risk_count=Count('id'),
            avg_risk=Avg('risk_score'),
        )
        .order_by('-avg_risk')[:limit]
    )


def get_grupos_criticos(
    campaign: Campaign,
    unidade_ids: list[int] | None = None,
    setor_ids: list[int] | None = None,
) -> dict[str, list[dict]]:
    """Average risk score grouped by gender and by age range."""
    qs = _base_qs(campaign, unidade_ids, setor_ids)

    by_gender = list(
        qs.exclude(gender__isnull=True)
        .values('gender')
        .annotate(avg_risk=Avg('risk_score'))
        .order_by('-avg_risk')
    )
    by_age_range = list(
        qs.exclude(age_range__isnull=True)
        .values('age_range')
        .annotate(avg_risk=Avg('risk_score'))
        .order_by('-avg_risk')
    )
    return {'by_gender': by_gender, 'by_age_range': by_age_range}


def get_filtros_disponiveis(
    campaign: Campaign,
    user,
) -> dict[str, list[dict]]:
    """
    Return the unidades and setores that *this user* is allowed to filter by
    for the given campaign.

    RH / GLOBAL_ADMIN  → all unidades/setores that appear in the campaign data.
    LEADER             → only the ones covered by their LeaderPermission rows.
    """
    from apps.users.models import UserRole
    from apps.organizational.models import LeaderPermission, Setor, Unidade

    # Unidade/Setor IDs that appear in this campaign's DimensionScore rows
    campaign_unidade_ids = set(
        DimensionScore.objects.filter(campaign=campaign)
        .exclude(unidade_id__isnull=True)
        .values_list('unidade_id', flat=True)
        .distinct()
    )
    campaign_setor_ids = set(
        DimensionScore.objects.filter(campaign=campaign)
        .exclude(setor_id__isnull=True)
        .values_list('setor_id', flat=True)
        .distinct()
    )

    if user.role in (UserRole.RH, UserRole.GLOBAL_ADMIN):
        allowed_unidade_ids = campaign_unidade_ids
        allowed_setor_ids = campaign_setor_ids
    else:
        # LEADER: intersect with their granted permissions
        from django.db.models import Q
        perms = LeaderPermission.objects.filter(user=user)
        unidade_all_ids = set(
            perms.filter(setor__isnull=True).values_list('unidade_id', flat=True)
        )
        setor_exact_ids = set(
            perms.filter(setor__isnull=False).values_list('setor_id', flat=True)
        )

        # Allowed unidades: those with "all setores" permission or explicit setor permission
        perm_unidade_ids = unidade_all_ids | set(
            perms.filter(setor__isnull=False).values_list('unidade_id', flat=True)
        )
        allowed_unidade_ids = campaign_unidade_ids & perm_unidade_ids

        # Allowed setores: setor belongs to allowed unidade (full access) OR explicit
        allowed_setor_ids_from_unidade = set(
            Setor.objects.filter(unidade_id__in=unidade_all_ids)
            .values_list('pk', flat=True)
        )
        allowed_setor_ids = campaign_setor_ids & (
            allowed_setor_ids_from_unidade | setor_exact_ids
        )

    unidades = list(
        Unidade.objects.filter(pk__in=allowed_unidade_ids).values('id', 'name').order_by('name')
    )
    setores = list(
        Setor.objects.filter(pk__in=allowed_setor_ids)
        .select_related('unidade')
        .values('id', 'name', 'unidade_id', 'unidade__name')
        .order_by('unidade__name', 'name')
    )

    return {'unidades': unidades, 'setores': setores}
