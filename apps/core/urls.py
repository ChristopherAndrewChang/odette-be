from django.urls import path
from .views import (
    ClubSettingsView,
    DonationSettingPublicView,
    DonationSettingAdminView,
    DonationSettingDetailView,
    DonationSettingActivateView,
    BannedWordListView,
    BannedWordDetailView,
)

urlpatterns = [
    path('settings/', ClubSettingsView.as_view()),
    path('settings/donation/', DonationSettingPublicView.as_view()),
    path('settings/donation/admin/', DonationSettingAdminView.as_view()),
    path('settings/donation/admin/<int:pk>/', DonationSettingDetailView.as_view()),
    path('settings/donation/admin/<int:pk>/activate/', DonationSettingActivateView.as_view()),
    path('banned-words/', BannedWordListView.as_view()),
    path('banned-words/<int:pk>/', BannedWordDetailView.as_view()),
]