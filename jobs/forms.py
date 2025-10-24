from django import forms
from .models import Job

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            "title",
            "company",
            "street_address",
            "city",
            "state",
            "zip_code",
            "country",
            "employment_type",
            "description",
            "requirements",
            "remote",
            "visa_sponsorship",
            "min_salary",
            "max_salary",
            "is_active",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Job Title",
            }),
            "company": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Company Name",
            }),
            "street_address": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "123 Main St",
            }),
            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Atlanta",
            }),
            "state": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Georgia",
            }),
            "zip_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "30332",
            }),
            "country": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "USA",
            }),
            "employment_type": forms.Select(attrs={
                "class": "form-select",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Job responsibilities, mission, etc.",
            }),
            "requirements": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Required skills, tools, experience...",
            }),
            "min_salary": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Minimum Salary",
            }),
            "max_salary": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Maximum Salary",
            }),

            # ✅ Dropdown replacements for Boolean fields
            "is_active": forms.Select(
                choices=[(True, "Active"), (False, "Inactive")],
                attrs={"class": "form-select"}
            ),
            "remote": forms.Select(
                choices=[(True, "Remote"), (False, "On-site")],
                attrs={"class": "form-select"}
            ),
            "visa_sponsorship": forms.Select(
                choices=[(True, "Visa Sponsorship"), (False, "No Sponsorship")],
                attrs={"class": "form-select"}
            ),
        }
