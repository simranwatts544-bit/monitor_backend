# Create your models here.
from django.db import models

class VM(models.Model):
    ip_address = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.ip_address

class Source(models.Model):
    name = models.CharField(max_length=200)
    profile = models.CharField(max_length=100)
    vm = models.ForeignKey(VM, on_delete=models.CASCADE, related_name='sources')
    is_keyword_based = models.BooleanField(default=False)
    is_profile_based = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.vm.ip_address}"
    
    class Meta:
        ordering = ['name']
        