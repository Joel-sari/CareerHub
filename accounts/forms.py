from django import forms
from django.contrib.auth.forms import UserCreationForm

from django.forms import inlineformset_factory

from .models import (
    User,
    JobSeekerProfile,
    RecruiterProfile,
    Education,
    Experience,
    RecruiterPreferences,
)

# -------------------------------------------------------
# SIGNUP FORM
# -------------------------------------------------------
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")


# -------------------------------------------------------
# JOB SEEKER PROFILE FORM
# -------------------------------------------------------
class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            "profile_picture",
            "full_name",
            "headline",
            "skills",
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
            "street_address": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "zip_code": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# -------------------------------------------------------
# EDUCATION FORM (MULTIPLE ENTRIES)
# -------------------------------------------------------
class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = [
            "school",
            "degree",
            "major",
            "start_year",
            "end_year",
            "currently_studying",
        ]
        widgets = {
            "school": forms.TextInput(attrs={"class": "form-control school-autocomplete"}),
            "degree": forms.TextInput(attrs={"class": "form-control"}),
            "major": forms.TextInput(attrs={"class": "form-control"}),
            "start_year": forms.NumberInput(attrs={"class": "form-control"}),
            "end_year": forms.NumberInput(attrs={"class": "form-control"}),
            "currently_studying": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# Formset — **multiple education entries**
EducationFormSet = inlineformset_factory(
    User,
    Education,
    form=EducationForm,
    extra=1,
    can_delete=True
)


# -------------------------------------------------------
# EXPERIENCE FORM (MULTIPLE ENTRIES)
# -------------------------------------------------------
class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = [
            "title",
            "company",
            "start_date",
            "end_date",
            "currently_working",
            "description",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "company": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "currently_working": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


# Formset — **multiple experience entries**
ExperienceFormSet = inlineformset_factory(
    User,
    Experience,
    form=ExperienceForm,
    extra=1,
    can_delete=True
)


# -------------------------------------------------------
# RECRUITER PROFILE FORM
# -------------------------------------------------------
class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = [
            "profile_picture",
            "company_name",
            "position",
        ]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.TextInput(attrs={"class": "form-control"}),
        }



# -------------------------------------------------------
# RECRUITER PREFERENCES FORM
# -------------------------------------------------------
class RecruiterPreferencesForm(forms.ModelForm):
    class Meta:
        model = RecruiterPreferences
        fields = [
            "preferred_degree",
            "preferred_major",
            "graduation_status",       # NEW
            "preferred_class_level",   # NEW
            "min_experience_years",
            "preferred_universities",
        ]
        labels = {
            "preferred_degree": "Preferred degree",
            "preferred_major": "Preferred major",
            "graduation_status": "Graduation status",
            "preferred_class_level": "Preferred class year (optional)",
            "min_experience_years": "Minimum years of experience",
            "preferred_universities": "Preferred universities (comma-separated)",
        }
        help_texts = {
            "graduation_status": "Do you want current students, graduates, or anyone?",
            "preferred_class_level": "If you care about class year (e.g., juniors), pick it here.",
        }