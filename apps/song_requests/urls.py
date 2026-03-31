from django.urls import path
from .views import SongRequestListView, SongRequestReviewView

urlpatterns = [
    path('', SongRequestListView.as_view()),
    path('<int:pk>/review/', SongRequestReviewView.as_view()),
]