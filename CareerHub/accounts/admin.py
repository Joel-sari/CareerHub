from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('isJobSeeker', 'isRecruiter')}),
    )
    list_display = ('username', 'email', 'isJobSeeker', 'isRecruiter', 'is_staff')

admin.site.register(User, CustomUserAdmin)
