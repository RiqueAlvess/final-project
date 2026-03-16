"""Authentication business logic services."""

import secrets
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User, PasswordResetToken
from .tasks import send_account_locked_email, send_password_reset_email

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Handles login, token generation, and security enforcement."""

    MAX_FAILED_ATTEMPTS = 3

    @classmethod
    def authenticate(cls, email: str, password: str) -> dict:
        """
        Authenticate a user with email and password.

        Returns a dict with 'access', 'refresh', and 'user' on success.
        Raises ValueError with a descriptive message on failure.
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValueError('Invalid credentials.')

        if not user.is_active:
            raise ValueError('Account is inactive.')

        if user.is_locked:
            raise ValueError('Account is locked. Check your email for instructions.')

        if not user.check_password(password):
            attempts = user.increment_failed_attempts()
            logger.warning(f'Failed login for {email}. Attempt {attempts}/{cls.MAX_FAILED_ATTEMPTS}')

            if attempts >= cls.MAX_FAILED_ATTEMPTS:
                user.lock_account()
                logger.warning(f'Account locked for {email} after {attempts} failed attempts.')
                # Send async lockout notification
                try:
                    send_account_locked_email.delay(user.id)
                except Exception as e:
                    logger.error(f'Failed to queue lockout email for {email}: {e}')
                raise ValueError('Account locked due to too many failed attempts. Check your email.')

            raise ValueError('Invalid credentials.')

        # Successful login
        user.reset_failed_attempts()
        tokens = cls._generate_tokens(user)
        return {**tokens, 'user': user}

    @staticmethod
    def _generate_tokens(user: User) -> dict:
        """Generate JWT access and refresh tokens."""
        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.role
        refresh['email'] = user.email
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def logout(refresh_token: str) -> None:
        """Blacklist the refresh token to invalidate the session."""
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            logger.warning(f'Error blacklisting token: {e}')


class PasswordResetService:
    """Handles Magic Link password reset flow."""

    TOKEN_EXPIRY_HOURS = getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY_HOURS', 24)

    @classmethod
    def request_reset(cls, email: str) -> None:
        """
        Generate a magic link token and send it via email.
        Does not reveal whether the email exists (security best practice).
        """
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Silently ignore: don't reveal if email exists
            logger.info(f'Password reset requested for non-existent email: {email}')
            return

        # Invalidate any existing unused tokens for this user
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)

        token = secrets.token_urlsafe(48)
        expires_at = timezone.now() + timedelta(hours=cls.TOKEN_EXPIRY_HOURS)

        PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at,
        )

        # Queue async email sending
        try:
            send_password_reset_email.delay(user.id, token)
        except Exception as e:
            logger.error(f'Failed to queue password reset email for {email}: {e}')

    @classmethod
    def confirm_reset(cls, token: str, new_password: str) -> None:
        """
        Validate the token and update the user's password.
        Raises ValueError if token is invalid or expired.
        """
        try:
            reset_token = PasswordResetToken.objects.select_related('user').get(token=token)
        except PasswordResetToken.DoesNotExist:
            raise ValueError('Invalid or expired reset token.')

        if not reset_token.is_valid:
            raise ValueError('Invalid or expired reset token.')

        user = reset_token.user
        user.set_password(new_password)
        user.unlock_account()
        user.save()

        reset_token.is_used = True
        reset_token.save(update_fields=['is_used'])

        logger.info(f'Password reset successfully for {user.email}')
