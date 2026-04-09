from django.urls import path
from .views import AdminAccountListCreateView, AdminAccountDetailView, MeView

urlpatterns = [
    path('admins/', AdminAccountListCreateView.as_view()),
    path('admins/<int:pk>/', AdminAccountDetailView.as_view()),
    path('me/', MeView.as_view()),
]

