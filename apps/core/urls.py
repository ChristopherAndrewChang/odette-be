from django.urls import path
from .views import ClubSettingsView

urlpatterns = [
    path('settings/', ClubSettingsView.as_view()),
]