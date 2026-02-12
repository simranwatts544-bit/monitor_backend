from django.urls import path
from .views import MonitoringViewSet

urlpatterns = [
    path('', MonitoringViewSet.as_view({'get': 'list'}), name='monitoring-list'),
]