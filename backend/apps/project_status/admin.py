from django.contrib import admin

from .models import ProjectPhase, ProjectModule


@admin.register(ProjectPhase)
class ProjectPhaseAdmin(admin.ModelAdmin):
    list_display = ['order', 'name', 'status', 'date_completed']
    list_display_links = ['name']
    list_editable = ['order', 'status']
    list_filter = ['status']
    search_fields = ['name', 'description']
    ordering = ['order']


@admin.register(ProjectModule)
class ProjectModuleAdmin(admin.ModelAdmin):
    list_display = ['order', 'name', 'status', 'icon']
    list_display_links = ['name']
    list_editable = ['order', 'status', 'icon']
    list_filter = ['status']
    search_fields = ['name', 'description']
    ordering = ['order']
