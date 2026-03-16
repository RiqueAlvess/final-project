"""User management views."""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import User
from .permissions import IsRH, IsAccountOwnerOrRH
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    MeSerializer,
)


class MeView(generics.RetrieveAPIView):
    """Return the authenticated user's profile."""

    permission_classes = (IsAuthenticated,)
    serializer_class = MeSerializer

    def get_object(self) -> User:
        return self.request.user


class UserListCreateView(generics.ListCreateAPIView):
    """List all users or create a new one (RH/GLOBAL_ADMIN only)."""

    permission_classes = (IsRH,)

    def get_queryset(self):
        return User.objects.filter(is_active=True).order_by('email')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer


class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a user."""

    permission_classes = (IsAuthenticated, IsAccountOwnerOrRH)

    def get_queryset(self):
        return User.objects.all()

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateSerializer
        return UserSerializer

    def perform_destroy(self, instance: User) -> None:
        # Soft delete: deactivate instead of deleting
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class ChangePasswordView(generics.GenericAPIView):
    """Allow users to change their own password."""

    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': 'Incorrect password.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'detail': 'Password changed successfully.'})
