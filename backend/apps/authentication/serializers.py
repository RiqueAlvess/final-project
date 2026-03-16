"""Authentication serializers."""

from rest_framework import serializers
from apps.users.models import User


class LoginSerializer(serializers.Serializer):
    """Serializer for email/password login."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})


class TokenResponseSerializer(serializers.Serializer):
    """Response serializer for successful login."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        from apps.users.serializers import MeSerializer
        return MeSerializer(obj['user']).data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request a password reset magic link."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirm password reset with token and new password."""

    from django.contrib.auth.password_validation import validate_password

    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        return attrs


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for token refresh."""

    refresh = serializers.CharField()
