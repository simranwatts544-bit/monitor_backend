from django.urls import path
from . import views

urlpatterns = [
    # VM URLs
    path('vms/', views.VMListView.as_view(), name='vm-list'),
    path('vms/<int:pk>/', views.VMDetailView.as_view(), name='vm-detail'),
    
    # Source URLs
    path('sources/', views.SourceListView.as_view(), name='source-list'),
    path('sources/<int:pk>/', views.SourceDetailView.as_view(), name='source-detail'),
    
    # Search URLs
    path('sources/search/', views.SourceSearchView.as_view(), name='source-search'),
    
    # Profile URLs
    path('profiles/', views.ProfileListView.as_view(), name='profile-list'),
]
