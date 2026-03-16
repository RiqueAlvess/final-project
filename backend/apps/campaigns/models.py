"""Campaign, HSE-IT survey and analytics models."""

import uuid

from django.conf import settings
from django.db import models


class Campaign(models.Model):
    """Organizational research campaign grouping invites, responses and dashboards."""

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Rascunho'
        ACTIVE = 'ACTIVE', 'Ativa'
        CLOSED = 'CLOSED', 'Encerrada'

    name = models.CharField(max_length=255, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Status',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns',
        verbose_name='Criado por',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Campanha'
        verbose_name_plural = 'Campanhas'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.name


class HSEDimension(models.Model):
    """One of the 7 HSE-IT dimensions."""

    class DimensionType(models.TextChoices):
        POSITIVE = 'POSITIVE', 'Positiva'   # low score → higher risk
        NEGATIVE = 'NEGATIVE', 'Negativa'   # high score → higher risk

    name = models.CharField(max_length=100, verbose_name='Nome')
    dimension_type = models.CharField(
        max_length=10,
        choices=DimensionType.choices,
        verbose_name='Tipo',
    )
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Ordem')

    class Meta:
        verbose_name = 'Dimensão HSE'
        verbose_name_plural = 'Dimensões HSE'
        ordering = ['order']

    def __str__(self) -> str:
        return self.name


class HSEQuestion(models.Model):
    """A single question belonging to an HSEDimension."""

    text = models.TextField(verbose_name='Texto da Pergunta')
    dimension = models.ForeignKey(
        HSEDimension,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Dimensão',
    )
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Ordem')

    class Meta:
        verbose_name = 'Pergunta HSE'
        verbose_name_plural = 'Perguntas HSE'
        ordering = ['dimension__order', 'order']

    def __str__(self) -> str:
        return f'[{self.dimension.name}] {self.text[:60]}'


class SurveyInvite(models.Model):
    """Anonymized invitation sent to a collaborator for a specific campaign."""

    class SendStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        SENT = 'SENT', 'Enviado'
        FAILED = 'FAILED', 'Falhou'

    class ResponseStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        ANSWERED = 'ANSWERED', 'Respondido'

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='invites',
        verbose_name='Campanha',
    )
    # LGPD: email is stored only as a deterministic HMAC-SHA256 hash
    email_hash = models.CharField(
        max_length=64,
        verbose_name='Hash do Email',
        db_index=True,
    )
    # Reference to the Registro for demographic data (unidade/setor)
    registro_id = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Registro ID'
    )
    unidade_id = models.PositiveIntegerField(
        null=True, blank=True, db_index=True, verbose_name='Unidade ID'
    )
    setor_id = models.PositiveIntegerField(
        null=True, blank=True, db_index=True, verbose_name='Setor ID'
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name='Token',
    )
    send_status = models.CharField(
        max_length=10,
        choices=SendStatus.choices,
        default=SendStatus.PENDING,
        verbose_name='Status de Envio',
    )
    response_status = models.CharField(
        max_length=10,
        choices=ResponseStatus.choices,
        default=ResponseStatus.PENDING,
        verbose_name='Status de Resposta',
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Enviado em')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Convite de Pesquisa'
        verbose_name_plural = 'Convites de Pesquisa'
        ordering = ['-created_at']
        unique_together = ('campaign', 'email_hash')

    def __str__(self) -> str:
        return f'Invite {self.token} [{self.send_status}/{self.response_status}]'

    @property
    def is_answered(self) -> bool:
        return self.response_status == self.ResponseStatus.ANSWERED


class SurveyResponse(models.Model):
    """Completed survey response linked to a one-time-use invite."""

    class Gender(models.TextChoices):
        MALE = 'M', 'Masculino'
        FEMALE = 'F', 'Feminino'
        OTHER = 'O', 'Outro'
        PREFER_NOT = 'P', 'Prefiro não dizer'

    class AgeRange(models.TextChoices):
        UP_TO_25 = 'UP_TO_25', 'Até 25 anos'
        AGE_26_35 = '26_35', '26–35 anos'
        AGE_36_45 = '36_45', '36–45 anos'
        AGE_46_55 = '46_55', '46–55 anos'
        ABOVE_55 = 'ABOVE_55', 'Acima de 55 anos'
        PREFER_NOT = 'PREF', 'Prefiro não dizer'

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name='Campanha',
    )
    invite = models.OneToOneField(
        SurveyInvite,
        on_delete=models.CASCADE,
        related_name='response',
        verbose_name='Convite',
    )
    gender = models.CharField(
        max_length=4,
        choices=Gender.choices,
        null=True,
        blank=True,
        verbose_name='Gênero',
    )
    age_range = models.CharField(
        max_length=20,
        choices=AgeRange.choices,
        null=True,
        blank=True,
        verbose_name='Faixa Etária',
    )
    consent_given = models.BooleanField(default=False, verbose_name='Consentimento dado')
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Resposta de Pesquisa'
        verbose_name_plural = 'Respostas de Pesquisa'
        ordering = ['-answered_at']

    def __str__(self) -> str:
        return f'Resposta para convite {self.invite.token}'


class SurveyAnswer(models.Model):
    """A single numeric answer (0–4) to one HSEQuestion within a SurveyResponse."""

    response = models.ForeignKey(
        SurveyResponse,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Resposta',
    )
    question = models.ForeignKey(
        HSEQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Pergunta',
    )
    value = models.PositiveSmallIntegerField(verbose_name='Valor')  # 0–4

    class Meta:
        verbose_name = 'Resposta de Pergunta'
        verbose_name_plural = 'Respostas de Perguntas'
        unique_together = ('response', 'question')

    def __str__(self) -> str:
        return f'Q{self.question_id}: {self.value}'


class DimensionScore(models.Model):
    """
    Pre-computed score per dimension per response.

    Acts as a star-schema fact table for dashboard analytics.
    Denormalized fields (campaign, unidade_id, setor_id, gender, age_range)
    allow efficient aggregation without joins.
    """

    class RiskLevel(models.TextChoices):
        ACCEPTABLE = 'ACEITAVEL', 'Aceitável'
        MODERATE = 'MODERADO', 'Moderado'
        IMPORTANT = 'IMPORTANTE', 'Importante'
        CRITICAL = 'CRITICO', 'Crítico'

    response = models.ForeignKey(
        SurveyResponse,
        on_delete=models.CASCADE,
        related_name='dimension_scores',
        verbose_name='Resposta',
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='dimension_scores',
        verbose_name='Campanha',
        db_index=True,
    )
    dimension = models.ForeignKey(
        HSEDimension,
        on_delete=models.CASCADE,
        related_name='scores',
        verbose_name='Dimensão',
    )
    score = models.DecimalField(
        max_digits=4, decimal_places=2, verbose_name='Score (0–4)'
    )
    risk_score = models.DecimalField(
        max_digits=4, decimal_places=2, verbose_name='Score de Risco (0–4)'
    )
    risk_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
        verbose_name='Nível de Risco',
        db_index=True,
    )
    # Denormalized for fast aggregation
    unidade_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    setor_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    gender = models.CharField(max_length=4, null=True, blank=True, db_index=True)
    age_range = models.CharField(max_length=20, null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = 'Score de Dimensão'
        verbose_name_plural = 'Scores de Dimensão'
        unique_together = ('response', 'dimension')
        indexes = [
            models.Index(fields=['campaign', 'dimension']),
            models.Index(fields=['campaign', 'risk_level']),
            models.Index(fields=['campaign', 'unidade_id', 'setor_id']),
        ]

    def __str__(self) -> str:
        return f'{self.dimension.name}: {self.score} (risco: {self.risk_level})'
