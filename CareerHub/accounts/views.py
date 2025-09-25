from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from django.contrib.auth import login



# Create your views here.

# Handles user login with a custom redirect based on the user account type
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        # Redirect to correct dashboard upon login
        user = self.request.user
        if user.isJobSeeker:
            return reverse('jobseeker_dashboard')
        elif user.isRecruiter:
            return reverse('recruiter_dashboard')
        return reverse('home')
        
@login_required
def jobseeker_dashboard(request):
    # Job seeker dashboard
    return render(request, 'accounts/jobseeker_dashboard.html')

@login_required
def recruiter_dashboard(request):
    # Recruiter dashboard
    return render(request, 'accounts/recruiter_dashboard.html')

def register_view(request):
    # Handles new user registrations
    # If form is valid, create user, log in, and redirect to correct dashboard
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.isJobSeeker:
                return redirect('jobseeker_dashboard')
            elif user.isRecruiter:
                return redirect('recruiter_dashboard')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})