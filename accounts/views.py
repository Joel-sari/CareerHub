from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponseForbidden
from django.core.mail import EmailMessage
from django.conf import settings
from django import forms
from django.db import models
from jobs.models import Job, Application
from django.utils import timezone
from urllib.parse import urlencode

from .models import User, JobSeekerProfile, CandidateSavedSearch

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
    user = request.user

    # Jobs the user applied to
    applications = Application.objects.filter(applicant=user).select_related('job')

    # Recommended jobs (example logic — nearby or unspecific for now)
    recommended_jobs = Job.objects.exclude(applications__applicant=user)[:3]

    return render(request, "accounts/jobseeker_dashboard.html", {
        "applications": applications,
        "recommended_jobs": recommended_jobs,
    })


@login_required
def recruiter_dashboard(request):
    user = request.user

    # Jobs posted by this recruiter
    jobs = Job.objects.filter(recruiter=user)

    # Applications to this recruiter's jobs
    applications = Application.objects.filter(job__recruiter=user).select_related("applicant", "job")

    # Saved candidate searches
    saved_searches = CandidateSavedSearch.objects.filter(owner=user)[:5]

    return render(request, "accounts/recruiter_dashboard.html", {
        "user": user,
        "jobs": jobs,
        "applications": applications,
        "saved_searches": saved_searches,
    })



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


@login_required
def my_applications(request):
    user = request.user
    applications = Application.objects.filter(applicant=user).select_related("job")

    return render(request, "accounts/my_applications.html", {
        "applications": applications,
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

@login_required
def recruiter_applicants_kanban(request):
    if request.user.role != User.RECRUITER:
        return HttpResponseForbidden("Only recruiters can view this page.")

    applications = Application.objects.filter(
        job__recruiter=request.user
    ).select_related("applicant", "job")

    backlog = applications.filter(status="applied")
    review = applications.filter(status="review")

    # All final decisions (hired/rejected) still remain under "closed"
    Closed = applications.filter(status="closed")

    # Remove hired column entirely
    Hired = Application.objects.none()

    return render(request, "accounts/applicants_recruiter_view.html", {
        "backlog": backlog,
        "review": review,
        "Closed": Closed,
        "Hired": Hired,   # Will be empty so the HTML section will disappear
    })


@login_required
def update_applicant_status(request, app_id):
    if request.method == "POST":
        new_status = request.POST.get("status")
        final_decision = request.POST.get("final_decision")  # NEW

        app = Application.objects.get(id=app_id)

        # Drag & drop moves columns
        if new_status in ["applied", "review", "closed"]:
            app.status = new_status  

        # Buttons update final decision only
        if final_decision in ["hired", "rejected"]:
            app.final_decision = final_decision

        app.save()
        return JsonResponse({"success": True})

# -------------------------------------------------------
# Saved Search Helpers
# -------------------------------------------------------

def extract_candidate_filters(query_dict):
    """
    Take request.GET or request.POST and return a plain dict
    of the filter fields we care about.
    """
    allowed_keys = ["name", "skills", "education", "location"]

    filters = {}
    for key in allowed_keys:
        value = query_dict.get(key, "").strip()
        if value:
            filters[key] = value

    # sort placeholder for UI
    sort = query_dict.get("sort")
    if sort:
        filters["sort"] = sort

    return filters


def build_default_search_name(filters):
    """
    Build a default human-readable label like:
    "Python • Atlanta • BS".
    """
    parts = []

    if "skills" in filters:
        parts.append(filters["skills"])
    if "location" in filters:
        parts.append(filters["location"])
    if "education" in filters:
        parts.append(filters["education"])
    if "name" in filters:
        parts.append(filters["name"])

    if not parts:
        return "All candidates"

    return " • ".join(parts)


# Candidate List (Recruiter only)
@login_required
def candidate_list(request):
    if request.user.role != User.RECRUITER:
        return HttpResponseForbidden("Only recruiters can view candidates.")

    # --- BASE QUERYSET ---
    candidates = JobSeekerProfile.objects.filter(is_public=True)

    # --- FILTER INPUTS ---
    name = request.GET.get("name", "").strip()
    skills = request.GET.get("skills", "").strip()
    education = request.GET.get("education", "").strip()
    location = request.GET.get("location", "").strip()

    # --- APPLY FILTERS ---
    if name:
        candidates = candidates.filter(user__username__icontains=name)

    if skills:
        candidates = candidates.filter(skills__icontains=skills)

    if education:
        candidates = candidates.filter(education__icontains=education)

    if location:
        candidates = candidates.filter(
            models.Q(city__icontains=location)
            | models.Q(state__icontains=location)
            | models.Q(country__icontains=location)
        )

    # --- CURRENT FILTERS DICT (for saving) ---
    current_filters = extract_candidate_filters(request.GET)

    # --- SAVED SEARCHES FOR THIS RECRUITER ---
    saved_searches = CandidateSavedSearch.objects.filter(owner=request.user)

    # --- RENDER TEMPLATE ---
    return render(request, "accounts/candidate_list.html", {
        "candidates": candidates,
        "saved_searches": saved_searches,
        "current_filters": current_filters,
    })




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
# Candidate Saved Searches (Recruiter)
# -------------------------------------------------------

@login_required
def create_candidate_saved_search(request):
    if request.user.role != User.RECRUITER:
        return HttpResponseForbidden("Only recruiters can save searches.")

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    filters = extract_candidate_filters(request.POST)
    sort_order = filters.get("sort", "")

    # Soft cap at 20
    existing_count = CandidateSavedSearch.objects.filter(owner=request.user).count()
    overwrite_id = request.POST.get("overwrite_id")

    if existing_count >= 20 and not overwrite_id:
        return JsonResponse(
            {
                "status": "error",
                "code": "soft_cap_reached",
                "message": "You’ve reached the limit of 20 saved searches.",
            },
            status=400,
        )

    name = request.POST.get("name", "").strip() or build_default_search_name(filters)

    # Overwrite existing
    if overwrite_id:
        saved = get_object_or_404(CandidateSavedSearch, pk=overwrite_id, owner=request.user)
        saved.name = name
        saved.filters = filters
        saved.sort_order = sort_order
        saved.updated_at = timezone.now()
        saved.save()
        return JsonResponse(
            {"status": "ok", "mode": "overwritten", "id": saved.id, "name": saved.name}
        )

    # Name collision detection
    existing = CandidateSavedSearch.objects.filter(owner=request.user, name=name).first()
    if existing:
        return JsonResponse(
            {
                "status": "collision",
                "message": f"You already have a search named “{name}”.",
                "existing_id": existing.id,
            },
            status=409,
        )

    saved = CandidateSavedSearch.objects.create(
        owner=request.user,
        name=name,
        filters=filters,
        sort_order=sort_order,
    )

    return JsonResponse(
        {"status": "ok", "mode": "created", "id": saved.id, "name": saved.name}
    )


@login_required
def rename_candidate_saved_search(request, pk):
    if request.user.role != User.RECRUITER:
        return HttpResponseForbidden("Only recruiters can rename searches.")

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    saved = get_object_or_404(CandidateSavedSearch, pk=pk, owner=request.user)
    new_name = request.POST.get("name", "").strip()
    if not new_name:
        return JsonResponse({"error": "Name required"}, status=400)

    saved.name = new_name
    saved.save(update_fields=["name", "updated_at"])
    return JsonResponse({"status": "ok", "id": saved.id, "name": saved.name})


@login_required
def update_candidate_saved_search_from_current(request, pk):
    if request.user.role != User.RECRUITER:
        return HttpResponseForbidden("Only recruiters can update searches.")

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    saved = get_object_or_404(CandidateSavedSearch, pk=pk, owner=request.user)
    filters = extract_candidate_filters(request.POST)
    sort_order = filters.get("sort", "")

    saved.filters = filters
    saved.sort_order = sort_order
    saved.updated_at = timezone.now()
    saved.save()
    return JsonResponse({"status": "ok", "id": saved.id})


@login_required
def delete_candidate_saved_search(request, pk):
    if request.user.role != User.RECRUITER:
        return HttpResponseForbidden("Only recruiters can delete searches.")

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    saved = get_object_or_404(CandidateSavedSearch, pk=pk, owner=request.user)
    saved.delete()
    return JsonResponse({"status": "ok"})


@login_required
def run_candidate_saved_search(request, pk):
    if request.user.role != User.RECRUITER:
        return HttpResponseForbidden("Only recruiters can run saved searches.")

    saved = get_object_or_404(CandidateSavedSearch, pk=pk, owner=request.user)
    saved.last_run_at = timezone.now()
    saved.save(update_fields=["last_run_at"])

    base_url = "/accounts/candidates/"  # or use reverse if you have a named URL
    # But better, if URL name is 'candidate_list':
    from django.urls import reverse
    base_url = reverse("candidate_list")

    qs = saved.filters
    query_string = urlencode(qs)
    if query_string:
        return redirect(f"{base_url}?{query_string}")
    return redirect(base_url)


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