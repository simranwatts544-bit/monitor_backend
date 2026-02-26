from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import VM, Source
from .serializers import VMSerializer, SourceSerializer, SourceListSerializer
from rest_framework.permissions import AllowAny
# VM CRUD Operations
class VMListView(generics.ListCreateAPIView):
    queryset = VM.objects.all()
    serializer_class = VMSerializer

class VMDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = VM.objects.all()
    serializer_class = VMSerializer

# Source CRUD Operations
class SourceListView(generics.ListCreateAPIView):
    serializer_class = SourceListSerializer
    
    def get_queryset(self):
        queryset = Source.objects.select_related('vm').all()
        profile = self.request.query_params.get('profile', None)
        vm_ip = self.request.query_params.get('vm_ip', None)
        
        if profile:
            queryset = queryset.filter(profile=profile)
        if vm_ip:
            queryset = queryset.filter(vm__ip_address=vm_ip)
            
        return queryset

class SourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Source.objects.select_related('vm').all()
    serializer_class = SourceSerializer

# Search functionality
class SourceSearchView(generics.ListAPIView):
    serializer_class = SourceListSerializer
    permission_classes = [AllowAny] 
    def get_queryset(self):
        queryset = Source.objects.select_related('vm').all()
        source_name = self.request.query_params.get('source_name', None)
        profile = self.request.query_params.get('profile', None)
        vm_ip = self.request.query_params.get('vm_ip', None)
        
        if source_name:
            queryset = queryset.filter(name__icontains=source_name)
        if profile:
            queryset = queryset.filter(profile=profile)
        if vm_ip:
            queryset = queryset.filter(vm__ip_address=vm_ip)
            
        return queryset

# Get all unique profiles for dropdown
class ProfileListView(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        profiles = Source.objects.values_list('profile', flat=True).distinct()
        return Response({'profiles': list(profiles)})
