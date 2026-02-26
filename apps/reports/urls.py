# backend/apps/reports/urls.py
from django.urls import path
from .views import ReportListView, get_custom_report, GenerateDailyReportView, get_report_data, serve_report_file

urlpatterns = [
    path('', ReportListView.as_view(), name='report-list'),
    path('<str:filename>/data/', get_report_data, name='report-data'),
    path('generate/', GenerateDailyReportView.as_view(), name='report-generate'),
    path('custom/', get_custom_report, name='report-custom'),
    path('<str:filename>', serve_report_file, name='report-file'),  # ✅ NEW: serves raw txt file
]