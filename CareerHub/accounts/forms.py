from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, JobSeekerProfile, RecruiterProfile

# -------------------------------------------------------
# This forms.py was created by Joel Sari, allows to customize Django's built in forms with much more detail,
# -------------------------------------------------------
# Extends Django's built-in UserCreationForm
# - Adds email
# - Adds role (Job Seeker or Recruiter)
# - Uses our custom User model
# -------------------------------------------------------
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")


# -------------------------------------------------------
# JobSeekerProfileForm
# -------------------------------------------------------
# Lets job seekers update their profile information
# (headline, skills, education, work experience, privacy setting).
# -------------------------------------------------------
class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = ("headline", "skills", "education", "work_experience", "is_public")


# -------------------------------------------------------
# RecruiterProfileForm
# -------------------------------------------------------
# Lets recruiters update their company information.
# -------------------------------------------------------
class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = ("company_name", "position")