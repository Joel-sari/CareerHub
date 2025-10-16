from django.shortcuts import render, redirect, get_object_or_404
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

import csv
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test


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

        if getattr(user, 'is_admin', False):
            return "/accounts/admin/users/"
        
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


# -------------------------------------------------------
# Recruiter → Candidate Features
# -------------------------------------------------------

# Candidate List (Recruiter only)
@login_required
def candidate_list(request):
    if request.user.role != User.RECRUITER:
        return HttpResponseForbidden("Only recruiters can view candidates.")
    
    candidates = JobSeekerProfile.objects.filter(is_public=True)
    return render(request, "accounts/candidate_list.html", {"candidates": candidates})


# Candidate Profile (Recruiter only)
@login_required
def candidate_profile(request, user_id):
    if request.user.role != User.RECRUITER:
        return HttpResponseForbidden("Only recruiters can view candidate profiles.")
    
    candidate = get_object_or_404(User, id=user_id, role=User.JOB_SEEKER)
    return render(request, "accounts/candidate_profile.html", {"candidate": candidate})


# Email Candidate (Recruiter only)
class EmailCandidateForm(forms.Form):
    subject = forms.CharField(max_length=255)
    message = forms.CharField(widget=forms.Textarea)


@login_required
def email_candidate(request, user_id):
    if request.user.role != User.RECRUITER:
        return HttpResponseForbidden("Only recruiters can email candidates.")
    
    candidate = get_object_or_404(User, id=user_id, role=User.JOB_SEEKER)

    if request.method == "POST":
        form = EmailCandidateForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]

            recruiter = request.user  # logged-in recruiter

            # Add recruiter info into the email body
            full_message = f"""
            Message from Recruiter: {recruiter.username} ({recruiter.email})

            {message}
            """

            # Build and send email
            email = EmailMessage(
                subject=subject,
                body=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,  # platform email
                to=[candidate.email],                    # candidate's email
                reply_to=[recruiter.email],              # reply goes to recruiter
            )

            email.send(fail_silently=False)

            return render(request, "accounts/email_sent.html", {"candidate": candidate})
    else:
        form = EmailCandidateForm()

    return render(request, "accounts/email_candidate.html", {
        "form": form,
        "candidate": candidate,
    })

# -------------------------------------------------------
# Admin Views
# -------------------------------------------------------

def admin_required(view_func):
    decorated_view_func = user_passes_test(
        lambda user: getattr(user, 'is_admin', False),
        login_url='/accounts/login/')(view_func)
    return decorated_view_func

# User List (JSON/HTML)
@admin_required
def admin_user_list(request):
    users = User.objects.all().values('id', 'username', 'email', 'role', 'is_admin')
    if request.GET.get('format') == 'json':
        return JsonResponse(list(users), safe=False)
    return render(request, "accounts/admin_user_list.html", {"users": users})

# Export Users as CSV
@admin_required
def export_users_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Email', 'Role', 'Is Admin'])

    for user in User.objects.all():
        writer.writerow([user.id, user.username, user.email, user.role, user.is_admin])

    return response