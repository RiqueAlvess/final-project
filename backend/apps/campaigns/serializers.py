"""Serializers for the campaigns domain."""

from rest_framework import serializers

from .models import (
    Campaign,
    DimensionScore,
    HSEDimension,
    HSEQuestion,
    SurveyAnswer,
    SurveyInvite,
    SurveyResponse,
)


class HSEQuestionSerializer(serializers.ModelSerializer):
    dimension_name = serializers.CharField(source='dimension.name', read_only=True)

    class Meta:
        model = HSEQuestion
        fields = ['id', 'text', 'dimension', 'dimension_name', 'order']


class HSEDimensionSerializer(serializers.ModelSerializer):
    questions = HSEQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = HSEDimension
        fields = ['id', 'name', 'dimension_type', 'order', 'questions']


class CampaignSerializer(serializers.ModelSerializer):
    total_invites = serializers.SerializerMethodField()
    total_answered = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'status',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
            'total_invites', 'total_answered',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_total_invites(self, obj: Campaign) -> int:
        return obj.invites.count()

    def get_total_answered(self, obj: Campaign) -> int:
        return obj.invites.filter(
            response_status=SurveyInvite.ResponseStatus.ANSWERED
        ).count()

    def get_created_by_name(self, obj: Campaign) -> str | None:
        return obj.created_by.get_full_name() if obj.created_by else None


class CampaignWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = ['name', 'description', 'status']


class SurveyInviteSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)

    class Meta:
        model = SurveyInvite
        fields = [
            'id', 'campaign', 'campaign_name',
            'email_hash', 'token',
            'send_status', 'response_status',
            'sent_at', 'created_at',
            'unidade_id', 'setor_id',
        ]
        read_only_fields = ['id', 'token', 'created_at']


# ── Public survey serializers ──────────────────────────────────────────────────

class SurveyAnswerInputSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    value = serializers.IntegerField(min_value=0, max_value=4)


class SurveySubmitSerializer(serializers.Serializer):
    consent = serializers.BooleanField()
    gender = serializers.ChoiceField(
        choices=SurveyResponse.Gender.choices + [('', '')],
        required=False,
        allow_blank=True,
    )
    age_range = serializers.ChoiceField(
        choices=SurveyResponse.AgeRange.choices + [('', '')],
        required=False,
        allow_blank=True,
    )
    answers = SurveyAnswerInputSerializer(many=True)

    def validate_consent(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError(
                'O consentimento é obrigatório para participar da pesquisa.'
            )
        return value

    def validate_answers(self, value: list) -> list:
        if not value:
            raise serializers.ValidationError('Pelo menos uma resposta é obrigatória.')
        return value


# ── Dashboard serializers ──────────────────────────────────────────────────────

class DashboardSummarySerializer(serializers.Serializer):
    total_invites = serializers.IntegerField()
    total_answered = serializers.IntegerField()
    adhesion_rate = serializers.FloatField()
    igrp = serializers.FloatField()
    high_risk_pct = serializers.FloatField()
    dimension_scores = serializers.ListField()
    risk_distribution = serializers.DictField()


class BulkSendSerializer(serializers.Serializer):
    invite_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
    )
