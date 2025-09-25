from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, JobSeekerProfile, RecruiterProfile

# Register the custom User model with the Django admin site using a customized UserAdmin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Extend the existing fieldsets to include the 'role' field for user roles
    fieldsets = BaseUserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
    # Display these fields in the user list view within the admin
    list_display = ("username", "email", "role", "is_staff", "is_superuser")

# Register the JobSeekerProfile model with the admin site for management
admin.site.register(JobSeekerProfile)
# Register the RecruiterProfile model with the admin site for management
admin.site.register(RecruiterProfile)