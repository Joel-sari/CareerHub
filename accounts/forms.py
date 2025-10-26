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
from django import forms
from .models import JobSeekerProfile, RecruiterProfile

class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            "headline",
            "skills",
            "education",
            "work_experience",
            "street_address",
            "city",
            "state",
            "zip_code",
            "country",
            "is_public",
        ]
        widgets = {
            "headline": forms.TextInput(attrs={"class": "form-control"}),
            "skills": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "education": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "work_experience": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "street_address": forms.TextInput(attrs={"class": "form-control", "placeholder": "123 Main St"}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "Atlanta"}),
            "state": forms.TextInput(attrs={"class": "form-control", "placeholder": "Georgia"}),
            "zip_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "30332"}),
            "country": forms.TextInput(attrs={"class": "form-control", "placeholder": "USA"}),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# -------------------------------------------------------
# RecruiterProfileForm
# -------------------------------------------------------
# Lets recruiters update their company information.
# -------------------------------------------------------
class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = ("company_name", "position")