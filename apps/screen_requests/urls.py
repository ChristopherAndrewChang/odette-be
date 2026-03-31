from django.urls import path
from .views import ScreenRequestListView, ScreenRequestReviewView, ScreenRequestDownloadView

urlpatterns = [
    path('', ScreenRequestListView.as_view()),
    path('<int:pk>/review/', ScreenRequestReviewView.as_view()),
    path('<int:pk>/download/', ScreenRequestDownloadView.as_view()),
]