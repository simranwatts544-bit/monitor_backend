from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import VM, Source

@admin.register(VM)
class VMAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'name', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['ip_address', 'name']

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'profile', 'vm', 'is_keyword_based', 'is_profile_based', 'created_at']
    list_filter = ['profile', 'is_keyword_based', 'is_profile_based', 'created_at']
    search_fields = ['name', 'profile']
    list_editable = ['profile', 'is_keyword_based', 'is_profile_based']
