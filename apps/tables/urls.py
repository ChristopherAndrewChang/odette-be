from django.urls import path
from .views import (
    TableListCreateView,
    TableBulkCreateView,
    TableDetailView,
    GenerateQRView,
    BulkGenerateQRView,
    OpenNightView,
    CloseNightView,
    ScanQRView,
)

urlpatterns = [
    path('', TableListCreateView.as_view()),
    path('bulk/', TableBulkCreateView.as_view()),
    path('bulk-qr/', BulkGenerateQRView.as_view()),
    path('open-night/', OpenNightView.as_view()),
    path('close-night/', CloseNightView.as_view()),
    path('scan/', ScanQRView.as_view()),
    path('<int:pk>/', TableDetailView.as_view()),
    path('<int:pk>/generate-qr/', GenerateQRView.as_view()),
]