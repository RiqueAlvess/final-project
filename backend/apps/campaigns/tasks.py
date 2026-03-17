"""Async Celery tasks for survey email dispatch and score computation."""

import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# ── Score computation (heavy analytics pipeline) ──────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def compute_dimension_scores(self, response_id: int) -> None:
    """
    Asynchronously compute and persist DimensionScore rows for a SurveyResponse.

    This task is enqueued immediately after a survey is submitted so that
    score calculation is never performed during the HTTP request cycle.
    The dashboard consumes the pre-computed DimensionScore rows via selectors.
    """
    from apps.campaigns.models import SurveyResponse
    from apps.campaigns.services import ScoreCalculationService

    try:
        response = SurveyResponse.objects.select_related(
            'invite', 'campaign'
        ).get(pk=response_id)
    except SurveyResponse.DoesNotExist:
        logger.error('SurveyResponse %s not found – skipping score computation', response_id)
        return

    try:
        scores = ScoreCalculationService.calculate_and_store(response)
        logger.info(
            'Computed %d DimensionScore rows for response %s (campaign %s)',
            len(scores),
            response_id,
            response.campaign_id,
        )
    except Exception as exc:
        logger.error(
            'Score computation failed for response %s: %s', response_id, exc
        )
        raise self.retry(exc=exc)


def _send_resend(to: str, subject: str, html: str) -> bool:
    import resend

    resend.api_key = settings.RESEND_API_KEY
    if not resend.api_key:
        logger.warning('RESEND_API_KEY not configured – email not sent to %s', to)
        return False
    try:
        response = resend.Emails.send({
            'from': settings.DEFAULT_FROM_EMAIL,
            'to': [to],
            'subject': subject,
            'html': html,
        })
        logger.info('Survey email sent to %s: %s', to, response)
        return True
    except Exception as exc:
        logger.error('Failed to send survey email to %s: %s', to, exc)
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_survey_email(self, invite_id: int) -> None:
    """
    Fetch the real email from Registro and send the magic-link survey invitation.
    Marks the invite as SENT or FAILED accordingly.
    """
    from apps.campaigns.models import SurveyInvite
    from apps.organizational.models import Registro

    try:
        invite = SurveyInvite.objects.select_related('campaign').get(pk=invite_id)
    except SurveyInvite.DoesNotExist:
        logger.error('SurveyInvite %s not found', invite_id)
        return

    if invite.is_answered:
        logger.info('Invite %s already answered – skipping email', invite_id)
        return

    # Retrieve the real email via Registro (never stored on the invite itself)
    if not invite.registro_id:
        logger.error('Invite %s has no registro_id – cannot send email', invite_id)
        invite.send_status = SurveyInvite.SendStatus.FAILED
        invite.save(update_fields=['send_status'])
        return

    try:
        registro = Registro.objects.get(pk=invite.registro_id)
    except Registro.DoesNotExist:
        logger.error('Registro %s not found for invite %s', invite.registro_id, invite_id)
        invite.send_status = SurveyInvite.SendStatus.FAILED
        invite.save(update_fields=['send_status'])
        return

    survey_url = f'{settings.FRONTEND_URL}/survey/{invite.token}'
    campaign_name = invite.campaign.name

    subject = f'Pesquisa de Clima Organizacional – {campaign_name}'
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px;">
            <h1 style="color: white; margin: 0; font-size: 24px;">Vivamente360</h1>
            <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 14px;">
                Pesquisa de Clima Organizacional
            </p>
        </div>

        <h2 style="color: #333; font-size: 20px;">Você foi convidado(a) para participar</h2>
        <p style="font-size: 16px; line-height: 1.6; color: #555;">
            Sua empresa está realizando a pesquisa <strong>{campaign_name}</strong> para mapear
            o clima organizacional e melhorar o ambiente de trabalho.
        </p>
        <p style="font-size: 16px; line-height: 1.6; color: #555;">
            Sua participação é <strong>voluntária</strong> e todas as respostas são
            <strong>anônimas e confidenciais</strong>.
        </p>

        <div style="text-align: center; margin: 35px 0;">
            <a href="{survey_url}"
               style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white; padding: 16px 40px; border-radius: 8px;
                      text-decoration: none; font-size: 16px; font-weight: bold;
                      display: inline-block;">
                Responder Pesquisa
            </a>
        </div>

        <p style="font-size: 13px; color: #888; line-height: 1.5;">
            Este link é pessoal, intransferível e pode ser utilizado apenas uma vez.<br>
            Caso prefira copiar o endereço:<br>
            <a href="{survey_url}" style="color: #667eea; word-break: break-all;">{survey_url}</a>
        </p>

        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="font-size: 12px; color: #bbb; text-align: center;">
            Plataforma Vivamente360 &mdash; dados tratados em conformidade com a LGPD.
        </p>
    </body>
    </html>
    """

    try:
        _send_resend(registro.email, subject, html)
        invite.send_status = SurveyInvite.SendStatus.SENT
        invite.sent_at = timezone.now()
        invite.save(update_fields=['send_status', 'sent_at'])
    except Exception as exc:
        invite.send_status = SurveyInvite.SendStatus.FAILED
        invite.save(update_fields=['send_status'])
        raise self.retry(exc=exc)
