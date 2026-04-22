from django.urls import path
from .views import SongRequestListView, AdminSongReviewView, DJSongReviewView, CashierBillSongView, SongRequestSummaryView

urlpatterns = [
    path('', SongRequestListView.as_view()),
    path('summary/', SongRequestSummaryView.as_view()),
    path('<int:pk>/admin-review/', AdminSongReviewView.as_view()),
    path('<int:pk>/dj-review/', DJSongReviewView.as_view()),
    path('<int:pk>/bill/', CashierBillSongView.as_view()),
]