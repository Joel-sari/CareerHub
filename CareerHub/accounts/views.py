from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect

@login_required
def jobseeker_dashboard(request):
    return render(request, "accounts/jobseeker_dashboard.html")

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponseForbidden
from django.core.mail import EmailMessage
from django.conf import settings
from django import forms

from .forms import SignUpForm, JobSeekerProfileForm, RecruiterProfileForm
from .models import User, JobSeekerProfile


# -------------------------------------------------------
# Sign Up View
# -------------------------------------------------------
def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

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
class CustomLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        user = self.request.user
        if user.role == User.JOB_SEEKER:
            return "/accounts/dashboard/jobseeker/"
        else:
            return "/accounts/dashboard/recruiter/"


# -------------------------------------------------------
# Dashboards
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


# -------------------------------------------------------
# Placeholder Views for Future Features
# -------------------------------------------------------
@login_required
def post_job_placeholder(request):
    return HttpResponse("Placeholder: Post Job page coming soon.")

@login_required
def view_candidates_placeholder(request):
    return HttpResponse("Placeholder: View Candidates page coming soon.")

@login_required
def search_jobs_placeholder(request):
    return HttpResponse("Placeholder: Job Search page coming soon.")
