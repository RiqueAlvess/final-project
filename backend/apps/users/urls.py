"""URL patterns for user management."""

from django.urls import path
from .views import (
    MeView,
    UserListCreateView,
    UserRetrieveUpdateDestroyView,
    ChangePasswordView,
)

app_name = 'users'

urlpatterns = [
    path('me/', MeView.as_view(), name='me'),
    path('', UserListCreateView.as_view(), name='user-list-create'),
    path('<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]
