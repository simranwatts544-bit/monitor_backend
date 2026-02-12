from django.urls import path
from .views import UserViewSet

urlpatterns = [
    path('login/', UserViewSet.as_view({'post': 'login'}), name='user-login'),
    path('logout/', UserViewSet.as_view({'post': 'logout'}), name='user-logout'),
    path('me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
]