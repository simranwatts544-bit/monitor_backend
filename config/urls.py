from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/monitoring/', include('apps.monitoring.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/logs/', include('apps.logs.urls')),
    
    # Serve React app
    # path('', TemplateView.as_view(template_name='index.html')),
    # path('<path:path>', TemplateView.as_view(template_name='index.html')),
]