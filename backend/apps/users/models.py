"""Custom User model with role-based access control."""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    GLOBAL_ADMIN = 'GLOBAL_ADMIN', 'Global Admin'
    RH = 'RH', 'RH'
    LEADER = 'LEADER', 'Leader'


class UserManager(BaseUserManager):
    """Custom manager for User model."""

    def _create_user(self, email: str, password: str, **extra_fields) -> 'User':
        if not email:
            raise ValueError('Email is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str = None, **extra_fields) -> 'User':
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields) -> 'User':
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.GLOBAL_ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for the multi-tenant SaaS platform.

    Roles:
    - GLOBAL_ADMIN: Full access including Django Admin
    - RH: Full frontend access, no Django Admin
    - LEADER: Limited frontend access, no Django Admin
    """

    email = models.EmailField(unique=True, verbose_name='Email')
    first_name = models.CharField(max_length=150, verbose_name='First Name')
    last_name = models.CharField(max_length=150, verbose_name='Last Name')
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.RH,
        verbose_name='Role'
    )
    is_active = models.BooleanField(default=True, verbose_name='Active')
    is_staff = models.BooleanField(default=False, verbose_name='Staff')

    # Security fields
    failed_login_attempts = models.PositiveIntegerField(default=0)
    is_locked = models.BooleanField(default=False, verbose_name='Account Locked')
    locked_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['email']

    def __str__(self) -> str:
        return f'{self.get_full_name()} <{self.email}>'

    def get_full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self) -> str:
        return self.first_name

    @property
    def is_global_admin(self) -> bool:
        return self.role == UserRole.GLOBAL_ADMIN

    @property
    def is_rh(self) -> bool:
        return self.role == UserRole.RH

    @property
    def is_leader(self) -> bool:
        return self.role == UserRole.LEADER

    def lock_account(self) -> None:
        """Lock the user account and record the lockout time."""
        self.is_locked = True
        self.locked_at = timezone.now()
        self.save(update_fields=['is_locked', 'locked_at'])

    def unlock_account(self) -> None:
        """Unlock the user account and reset failed attempts."""
        self.is_locked = False
        self.locked_at = None
        self.failed_login_attempts = 0
        self.save(update_fields=['is_locked', 'locked_at', 'failed_login_attempts'])

    def increment_failed_attempts(self) -> int:
        """Increment failed login attempts counter."""
        self.failed_login_attempts += 1
        self.save(update_fields=['failed_login_attempts'])
        return self.failed_login_attempts

    def reset_failed_attempts(self) -> None:
        """Reset failed login attempts on successful login."""
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.save(update_fields=['failed_login_attempts'])


class PasswordResetToken(models.Model):
    """Magic link token for password reset."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Token for {self.user.email} (used: {self.is_used})'

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired
