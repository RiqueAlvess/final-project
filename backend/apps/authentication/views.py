"""Authentication views with rate limiting and security."""

import logging

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from .services import AuthenticationService, PasswordResetService

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """
    Login endpoint with rate limiting (3 attempts/minute per IP).
    Returns JWT access and refresh tokens.
    """

    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    @method_decorator(ratelimit(key='ip', rate='3/m', method='POST', block=True))
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            result = AuthenticationService.authenticate(email, password)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )

        from apps.users.serializers import MeSerializer
        return Response({
            'access': result['access'],
            'refresh': result['refresh'],
            'user': MeSerializer(result['user']).data,
        })


class LogoutView(APIView):
    """Logout endpoint: blacklists the refresh token."""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        AuthenticationService.logout(refresh_token)
        return Response({'detail': 'Logged out successfully.'})


class PasswordResetRequestView(APIView):
    """
    Request a magic link for password reset.
    Always returns 200 to avoid revealing whether the email exists.
    """

    permission_classes = (AllowAny,)

    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True))
    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        PasswordResetService.request_reset(serializer.validated_data['email'])

        return Response({
            'detail': 'If this email is registered, you will receive a password reset link shortly.'
        })


class PasswordResetConfirmView(APIView):
    """Confirm password reset using the magic link token."""

    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            PasswordResetService.confirm_reset(
                token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password'],
            )
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({'detail': 'Password reset successfully. You can now log in.'})


class TokenRefreshViewCustom(TokenRefreshView):
    """Custom token refresh view (extends simplejwt's)."""
    pass
