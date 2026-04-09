from django.urls import path
from .views import (
    MainCategoryListCreateView, MainCategoryDetailView,
    SubCategoryListCreateView, SubCategoryDetailView,
    MenuItemListCreateView, MenuItemDetailView,
    ExportCategoriesView, ImportCategoriesView,
    ExportMenuItemsView, ImportMenuItemsView,
    MenuPDFUploadView, MenuPDFListView, MenuPDFToggleView,
)

urlpatterns = [
    path('categories/', MainCategoryListCreateView.as_view()),
    path('categories/export/', ExportCategoriesView.as_view(), name='export-categories'),
    path('categories/import/', ImportCategoriesView.as_view(), name='import-categories'),
    path('categories/<int:pk>/', MainCategoryDetailView.as_view()),
    path('sub-categories/', SubCategoryListCreateView.as_view()),
    path('sub-categories/<int:pk>/', SubCategoryDetailView.as_view()),
    path('items/', MenuItemListCreateView.as_view()),
    path('items/export/', ExportMenuItemsView.as_view(), name='export-menu-items'),
    path('items/import/', ImportMenuItemsView.as_view(), name='import-menu-items'),
    path('items/<int:pk>/', MenuItemDetailView.as_view()),
    path('pdf/upload/', MenuPDFUploadView.as_view()),
    path('pdf/<str:pdf_type>/', MenuPDFListView.as_view()),
    path('pdf/<int:pk>/toggle/', MenuPDFToggleView.as_view()),
]