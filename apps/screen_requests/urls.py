from django.urls import path
from .views import (
    ScreenRequestListView,
    ScreenRequestReviewView,
    ScreenRequestMarkPlayedView,
    ScreenRequestDownloadView,
    MidtransWebhookView,
    ScreenRequestBillView
)

urlpatterns = [
    path('', ScreenRequestListView.as_view()),
    path('<int:pk>/review/', ScreenRequestReviewView.as_view()),
    path('<int:pk>/played/', ScreenRequestMarkPlayedView.as_view()),
    path('<int:pk>/download/', ScreenRequestDownloadView.as_view()),
    path('<int:pk>/bill/', ScreenRequestBillView.as_view()),
    path('webhook/midtrans/', MidtransWebhookView.as_view()),
]