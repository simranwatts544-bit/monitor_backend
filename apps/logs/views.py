from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class LogViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    def list(self, request):
        return Response({"message": "Logs API"})