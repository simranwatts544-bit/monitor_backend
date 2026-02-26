from rest_framework import serializers
from .models import VM, Source

class VMSerializer(serializers.ModelSerializer):
    class Meta:
        model = VM
        fields = ['id', 'ip_address', 'name', 'created_at', 'updated_at']

class SourceSerializer(serializers.ModelSerializer):
    vm_ip = serializers.CharField(source='vm.ip_address', read_only=True)
    vm_name = serializers.CharField(source='vm.name', read_only=True)
    
    class Meta:
        model = Source
        fields = ['id', 'name', 'profile', 'vm', 'vm_ip', 'vm_name', 
                 'is_keyword_based', 'is_profile_based', 'created_at', 'updated_at']

class SourceListSerializer(serializers.ModelSerializer):
    vm_ip = serializers.CharField(source='vm.ip_address', read_only=True)
    
    class Meta:
        model = Source
        fields = ['id', 'name', 'profile', 'vm_ip', 'is_keyword_based', 'is_profile_based']
