from django.urls import path
from .views import SongRequestListView, AdminSongReviewView, DJSongReviewView

urlpatterns = [
    path('', SongRequestListView.as_view()),
    path('<int:pk>/admin-review/', AdminSongReviewView.as_view()),
    path('<int:pk>/dj-review/', DJSongReviewView.as_view()),
]