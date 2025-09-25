from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    # Define the choices for the type of account a user can create
    # (job seeker and recruiter)
    ACCOUNT_TYPE_CHOICES = [
        ('job_seeker', 'I am seeking a job!'),
        ('recruiter', 'I am looking for applicants!'),
    ]

    # Create radio buttons
    account_type = forms.ChoiceField(
        choices=ACCOUNT_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label="What type of account are you making?"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'account_type')

    # Flags isJobSeeker or isRecruiter based on the selected acccount type
    def save(self, commit=True):
        user = super().save(commit=False)
        account_type = self.cleaned_data['account_type']
        if account_type == 'job_seeker':
            user.isJobSeeker = True
            user.isRecruiter = False
        else:
            user.isJobSeeker = False
            user.isRecruiter = True
        if commit:
            user.save()
        return user