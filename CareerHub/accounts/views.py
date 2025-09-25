from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect

@login_required
def jobseeker_dashboard(request):
    return render(request, "accounts/jobseeker_dashboard.html")

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from .forms import SignUpForm, JobSeekerProfileForm, RecruiterProfileForm
from .models import User


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
            # Save user to DB (creates User + linked profile via signals)
            user = form.save()

            # Log the user in so they don’t need to login again right after signup (built in function)
            login(request, user)

            # Redirect user based on role to fill in more profile info
            if user.role == User.JOB_SEEKER:
                return redirect("jobseeker_onboarding")
            else:
                return redirect("recruiter_onboarding")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


# -------------------------------------------------------
# Custom Login View
# -------------------------------------------------------
# Overrides Django’s built-in LoginView.
# After login, user is redirected based on their role.
# -------------------------------------------------------
class CustomLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        user = self.request.user
        if user.role == User.JOB_SEEKER:
            return "/accounts/dashboard/jobseeker/"
        else:
            return "/accounts/dashboard/recruiter/"


# -------------------------------------------------------
# Dashboards (Job Seeker / Recruiter)
# -------------------------------------------------------
# Each role sees its own dashboard.
# (Later you can expand these to show jobs, applications, etc.)
# -------------------------------------------------------
@login_required
def jobseeker_dashboard(request):
    return render(request, "accounts/jobseeker_dashboard.html")

@login_required
def recruiter_dashboard(request):
    return render(request, "accounts/recruiter_dashboard.html")


# -------------------------------------------------------
# Onboarding Views
# -------------------------------------------------------
# After signup, users fill out more details.
# These forms update the profiles created by signals in models.py.
# -------------------------------------------------------
@login_required
def jobseeker_onboarding(request):
    # Attach to current user’s profile
    form = JobSeekerProfileForm(
        request.POST or None,
        instance=getattr(request.user, "jobseeker", None)
    )
    if request.method == "POST" and form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()
        return redirect("jobseeker_dashboard")

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
        return redirect("recruiter_dashboard")

    return render(request, "accounts/recruiter_profile_form.html", {
        "form": form,
        "title": "Complete your Recruiter profile"
    })
