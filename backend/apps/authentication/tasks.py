"""Async Celery tasks for email sending via Resend API."""

import logging
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


def _send_email_via_resend(to: str, subject: str, html_content: str) -> bool:
    """Send an email using the Resend API."""
    import resend

    resend.api_key = settings.RESEND_API_KEY

    if not resend.api_key:
        logger.warning('RESEND_API_KEY not configured. Email not sent.')
        return False

    try:
        params = {
            'from': settings.DEFAULT_FROM_EMAIL,
            'to': [to],
            'subject': subject,
            'html': html_content,
        }
        response = resend.Emails.send(params)
        logger.info(f'Email sent to {to}: {response}')
        return True
    except Exception as e:
        logger.error(f'Failed to send email to {to}: {e}')
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_account_locked_email(self, user_id: int) -> None:
    """Send account lockout notification email."""
    from apps.users.models import User

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f'User {user_id} not found for lockout email.')
        return

    subject = 'Your account has been locked'
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
            <h1 style="color: white; margin: 0; font-size: 28px;">Security Alert</h1>
        </div>
        <h2 style="color: #333;">Hello, {user.get_full_name()}</h2>
        <p style="color: #555; font-size: 16px;">
            Your account has been <strong style="color: #e74c3c;">locked</strong> due to
            {settings.LOGIN_MAX_ATTEMPTS} consecutive failed login attempts.
        </p>
        <p style="color: #555; font-size: 16px;">
            If this was you, you can unlock your account by resetting your password.
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{settings.FRONTEND_URL}/auth/forgot-password"
               style="background: #667eea; color: white; padding: 15px 30px; border-radius: 8px;
                      text-decoration: none; font-size: 16px; font-weight: bold;">
                Reset Password
            </a>
        </div>
        <p style="color: #999; font-size: 14px;">
            If you did not attempt to log in, please contact your administrator immediately.
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #bbb; font-size: 12px; text-align: center;">
            This is an automated security notification. Do not reply to this email.
        </p>
    </body>
    </html>
    """

    try:
        _send_email_via_resend(user.email, subject, html_content)
    except Exception as exc:
        logger.error(f'Error sending lockout email to {user.email}: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email(self, user_id: int, token: str) -> None:
    """Send magic link password reset email."""
    from apps.users.models import User

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f'User {user_id} not found for password reset email.')
        return

    reset_url = f'{settings.FRONTEND_URL}/auth/reset-password?token={token}'
    subject = 'Reset your password'
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
            <h1 style="color: white; margin: 0; font-size: 28px;">Reset Your Password</h1>
        </div>
        <h2 style="color: #333;">Hello, {user.get_full_name()}</h2>
        <p style="color: #555; font-size: 16px;">
            You requested a password reset. Click the button below to set a new password.
        </p>
        <p style="color: #888; font-size: 14px;">
            This link is valid for <strong>{settings.PASSWORD_RESET_TOKEN_EXPIRY_HOURS} hours</strong>
            and can only be used once.
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}"
               style="background: #667eea; color: white; padding: 15px 30px; border-radius: 8px;
                      text-decoration: none; font-size: 16px; font-weight: bold;">
                Reset Password
            </a>
        </div>
        <p style="color: #999; font-size: 14px;">
            Or copy this link to your browser:<br>
            <a href="{reset_url}" style="color: #667eea; word-break: break-all;">{reset_url}</a>
        </p>
        <p style="color: #999; font-size: 14px;">
            If you did not request a password reset, you can safely ignore this email.
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #bbb; font-size: 12px; text-align: center;">
            This is an automated email. Do not reply to this email.
        </p>
    </body>
    </html>
    """

    try:
        _send_email_via_resend(user.email, subject, html_content)
    except Exception as exc:
        logger.error(f'Error sending password reset email to {user.email}: {exc}')
        raise self.retry(exc=exc)
