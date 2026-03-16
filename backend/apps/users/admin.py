"""Admin configuration for users."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_locked', 'date_joined')
    list_filter = ('role', 'is_active', 'is_locked', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('date_joined', 'last_login', 'locked_at', 'failed_login_attempts')

    fieldsets = (
        ('Authentication', {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Role & Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Security', {
            'fields': ('is_locked', 'locked_at', 'failed_login_attempts'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )

    actions = ['lock_selected_users', 'unlock_selected_users']

    def lock_selected_users(self, request, queryset):
        for user in queryset:
            user.lock_account()
        self.message_user(request, f'{queryset.count()} users locked.')

    lock_selected_users.short_description = 'Lock selected users'

    def unlock_selected_users(self, request, queryset):
        for user in queryset:
            user.unlock_account()
        self.message_user(request, f'{queryset.count()} users unlocked.')

    unlock_selected_users.short_description = 'Unlock selected users'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used',)
    search_fields = ('user__email',)
    readonly_fields = ('token', 'created_at')
