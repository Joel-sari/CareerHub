# Import AbstractUser from Django
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

# User already inherits the following feilds from Django User:
# username, email, first name, last name, password, date_joined
# is_active, is_staff, is_superuser
class User(AbstractUser):
    isJobSeeker = models.BooleanField(default = False)
    isRecruiter = models.BooleanField(default = False)