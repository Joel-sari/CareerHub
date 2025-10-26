# jobs/admin.py
from django.contrib import admin
from .models import Job, Application

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company",
        "location",
        "employment_type",
        "remote",
        "visa_sponsorship",
        "is_active",
        "recruiter",
        "created_at",
    )
    list_filter = (
        "employment_type",
        "remote",
        "visa_sponsorship",
        "is_active",
        "created_at",
    )
    search_fields = ("title", "company", "location", "description", "requirements")

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "applicant", "status", "applied_at")
    list_filter = ("status", "applied_at")
    search_fields = ("job__title", "applicant__username")
