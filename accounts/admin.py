from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import User, JobSeekerProfile, RecruiterProfile


# -------------------------------
# Resources (define which fields to export)
# -------------------------------

class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'is_staff', 'is_superuser')


class JobSeekerProfileResource(resources.ModelResource):
    class Meta:
        model = JobSeekerProfile
        fields = ('id', 'user__username', 'headline', 'skills', 'education', 'work_experience', 'is_public')


class RecruiterProfileResource(resources.ModelResource):
    class Meta:
        model = RecruiterProfile
        fields = ('id', 'user__username', 'company_name', 'position')


# -------------------------------
# Admin Classes
# -------------------------------

@admin.register(User)
class UserAdmin(ImportExportModelAdmin, BaseUserAdmin):
    resource_class = UserResource
    fieldsets = BaseUserAdmin.fieldsets + (("Role", {"fields": ("role", "is_admin")}),)
    list_display = ("username", "email", "role", "is_staff", "is_superuser", "is_admin")


@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(ImportExportModelAdmin):
    resource_class = JobSeekerProfileResource
    list_display = ('user', 'headline', 'is_public')


@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(ImportExportModelAdmin):
    resource_class = RecruiterProfileResource
    list_display = ('user', 'company_name', 'position')
