from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import SignUpForm, JobSeekerProfileForm, RecruiterProfileForm
from .models import User
from CareerHub.models import Job
from jobs.models import Job

# -------------------------------------------------------
# Sign Up View. This holds our "API"
# -------------------------------------------------------
# Handles user registration.
# - Uses SignUpForm (username, email, password, role).
# - After successful signup, logs the user in immediately.
# - Redirects to the correct onboarding page depending on role.
# -------------------------------------------------------
def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # ✅ namespaced redirects
            if user.role == User.JOB_SEEKER or user.role == "job_seeker":
                return redirect("accounts:jobseeker_onboarding")
            else:
                return redirect("accounts:recruiter_onboarding")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


# -------------------------------------------------------
# Custom Login View
# -------------------------------------------------------
class CustomLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        user = self.request.user
        if user.role == User.JOB_SEEKER or user.role == "job_seeker":
            # ✅ use reverse for clarity + namespace
            return reverse("accounts:jobseeker_dashboard")
        else:
            return reverse("accounts:recruiter_dashboard")


# -------------------------------------------------------
# Dashboards
# -------------------------------------------------------
@login_required
def jobseeker_dashboard(request):
    if request.user.role != User.JOB_SEEKER and request.user.role != "job_seeker":
        return redirect('home:home')  # ✅ namespaced home
    jobs = Job.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'accounts/jobseeker_dashboard.html', {'jobs': jobs})

@login_required
def recruiter_dashboard(request):
    return render(request, "accounts/recruiter_dashboard.html")


# -------------------------------------------------------
# Onboarding Views
# -------------------------------------------------------
@login_required
def jobseeker_onboarding(request):
    form = JobSeekerProfileForm(
        request.POST or None,
        instance=getattr(request.user, "jobseeker", None)
    )
    if request.method == "POST" and form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()
        return redirect("accounts:jobseeker_dashboard")  # ✅ namespaced
    return render(request, "accounts/jobseeker_profile_form.html", {
        "form": form,
        "title": "Complete your Job Seeker profile"
    })

@login_required
def recruiter_onboarding(request):
    form = RecruiterProfileForm(
        request.POST or None,
        instance=getattr(request.user, "recruiter", None)
    )
    if request.method == "POST" and form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()
        return redirect("accounts:recruiter_dashboard")  # ✅ namespaced
    return render(request, "accounts/recruiter_profile_form.html", {
        "form": form,
        "title": "Complete your Recruiter profile"
    })
