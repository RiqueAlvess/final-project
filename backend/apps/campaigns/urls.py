"""URL patterns for the campaigns app."""

from django.urls import path

from .views import (
    BulkSendInvitesView,
    CampaignActivateView,
    CampaignCloseView,
    CampaignDashboardView,
    CampaignDetailView,
    CampaignListCreateView,
    CreateInvitesFromRegistrosView,
    InviteListView,
    SurveySubmitView,
    SurveyTokenValidateView,
)

urlpatterns = [
    # Campaigns CRUD
    path('', CampaignListCreateView.as_view(), name='campaign-list-create'),
    path('<int:pk>/', CampaignDetailView.as_view(), name='campaign-detail'),
    path('<int:pk>/activate/', CampaignActivateView.as_view(), name='campaign-activate'),
    path('<int:pk>/close/', CampaignCloseView.as_view(), name='campaign-close'),

    # Invites management
    path('<int:campaign_pk>/invites/', InviteListView.as_view(), name='invite-list'),
    path('<int:pk>/invites/import/', CreateInvitesFromRegistrosView.as_view(), name='invite-import'),
    path('<int:pk>/invites/send/', BulkSendInvitesView.as_view(), name='invite-send'),

    # Dashboard
    path('<int:pk>/dashboard/', CampaignDashboardView.as_view(), name='campaign-dashboard'),

    # Public survey (no auth)
    path('survey/<str:token>/', SurveyTokenValidateView.as_view(), name='survey-validate'),
    path('survey/<str:token>/submit/', SurveySubmitView.as_view(), name='survey-submit'),
]
