from django.contrib import admin
from .models import Job, Application

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "employment_type", "is_active", "recruiter", "created_at")
    list_filter = ("employment_type", "is_active", "created_at")
    search_fields = ("title", "company", "location", "description", "requirements")

admin.site.register(Application)
