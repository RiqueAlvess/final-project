"""Django admin configuration for campaigns app."""

from django.contrib import admin

from .models import (
    Campaign,
    DimensionScore,
    HSEDimension,
    HSEQuestion,
    SurveyAnswer,
    SurveyInvite,
    SurveyResponse,
)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_by', 'created_at']
    list_filter = ['status']
    search_fields = ['name']


class HSEQuestionInline(admin.TabularInline):
    model = HSEQuestion
    extra = 0


@admin.register(HSEDimension)
class HSEDimensionAdmin(admin.ModelAdmin):
    list_display = ['name', 'dimension_type', 'order']
    inlines = [HSEQuestionInline]


@admin.register(HSEQuestion)
class HSEQuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'dimension', 'order']
    list_filter = ['dimension']


@admin.register(SurveyInvite)
class SurveyInviteAdmin(admin.ModelAdmin):
    list_display = ['token', 'campaign', 'email_hash', 'send_status', 'response_status', 'sent_at']
    list_filter = ['campaign', 'send_status', 'response_status']
    readonly_fields = ['token', 'email_hash']


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['invite', 'campaign', 'gender', 'age_range', 'answered_at']
    list_filter = ['campaign', 'gender']


@admin.register(SurveyAnswer)
class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ['response', 'question', 'value']


@admin.register(DimensionScore)
class DimensionScoreAdmin(admin.ModelAdmin):
    list_display = ['dimension', 'campaign', 'score', 'risk_score', 'risk_level']
    list_filter = ['campaign', 'dimension', 'risk_level']
