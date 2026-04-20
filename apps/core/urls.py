from django.urls import path
from .views import ClubSettingsView, DonationSettingPublicView, DonationSettingAdminView

urlpatterns = [
    path('settings/', ClubSettingsView.as_view()),
    path('settings/donation/', DonationSettingPublicView.as_view()),
    path('settings/donation/admin/', DonationSettingAdminView.as_view()),
]