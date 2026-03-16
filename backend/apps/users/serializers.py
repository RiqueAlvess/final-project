"""Serializers for user models."""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, UserRole


class LeaderPermissionBriefSerializer(serializers.Serializer):
    """Minimal representation of a leader's organizational permission."""
    id = serializers.IntegerField()
    unidade = serializers.IntegerField(source='unidade_id')
    unidade_name = serializers.CharField(source='unidade.name')
    setor = serializers.SerializerMethodField()
    setor_name = serializers.SerializerMethodField()

    def get_setor(self, obj) -> int | None:
        return obj.setor_id

    def get_setor_name(self, obj) -> str | None:
        return obj.setor.name if obj.setor else None


class UserSerializer(serializers.ModelSerializer):
    """Full user representation."""

    full_name = serializers.SerializerMethodField()
    leader_permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'is_locked', 'date_joined', 'last_login',
            'leader_permissions',
        )
        read_only_fields = ('id', 'date_joined', 'last_login', 'is_locked')

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name()

    def get_leader_permissions(self, obj: User):
        if obj.role != UserRole.LEADER:
            return []
        perms = obj.leader_permissions.select_related('unidade', 'setor').all()
        return LeaderPermissionBriefSerializer(perms, many=True).data


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'password', 'password_confirm')

    def validate(self, attrs: dict) -> dict:
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user data."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'role', 'is_active')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        return attrs


class MeSerializer(serializers.ModelSerializer):
    """Serializer for the authenticated user's own profile."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'date_joined', 'last_login'
        )
        read_only_fields = fields

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name()
