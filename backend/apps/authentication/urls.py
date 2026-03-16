"""URL patterns for authentication."""

from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    TokenRefreshViewCustom,
)

app_name = 'authentication'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshViewCustom.as_view(), name='token-refresh'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
