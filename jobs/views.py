# jobs/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

# If your team keeps models in CareerHub.models, make sure jobs/models.py re-exports them:
# from CareerHub.models import Job, Application
# Otherwise, just import from the local app:
from .models import Job, Application

from accounts.models import User
from .forms import JobForm
from .decorators import recruiter_required

@login_required
@recruiter_required
def jobs_create(request):
    form = JobForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.recruiter = request.user
        job.save()
        return redirect(job.get_absolute_url())
    return render(request, "jobs/job_form.html", {"form": form, "title": "Post a Job"})

@login_required
@recruiter_required
def jobs_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    form = JobForm(request.POST or None, instance=job)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(job.get_absolute_url())
    return render(request, "jobs/job_form.html", {"form": form, "title": f"Edit: {job.title}"})

@login_required
@recruiter_required
def jobs_my_list(request):
    jobs = Job.objects.filter(recruiter=request.user)
    return render(request, "jobs/job_list_mine.html", {"jobs": jobs, "title": "My Job Posts"})

def job_list(request):
    jobs = Job.objects.filter(is_active=True)
    applied_job_ids = []

    if request.user.is_authenticated and getattr(request.user, "role", None) == User.JOB_SEEKER:
        applied_job_ids = list(
            Application.objects.filter(applicant=request.user).values_list("job_id", flat=True)
        )

    for job in jobs:
        job.applied = job.id in applied_job_ids

    return render(request, "jobs/job_list.html", {"jobs": jobs})

def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)

    applied = False
    if request.user.is_authenticated and getattr(request.user, "role", None) == User.JOB_SEEKER:
        applied = Application.objects.filter(job=job, applicant=request.user).exists()

    return render(request, "jobs/job_detail.html", {
        "job": job,
        "applied": applied,
    })

@login_required
def apply_to_job(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)

    # Only job seekers can apply
    if getattr(request.user, "role", None) != User.JOB_SEEKER:
        raise PermissionDenied("Only job seekers can apply for jobs.")

    # Prevent duplicate applications
    if Application.objects.filter(job=job, applicant=request.user).exists():
        return render(request, "jobs/apply_form.html", {
            "job": job,
            "error": "You have applied for this job."
        })

    if request.method == "POST":
        note = request.POST.get("note", "").strip()
        Application.objects.create(job=job, applicant=request.user, note=note)
        return redirect("jobs:job_detail", pk=job.pk)

    return render(request, "jobs/apply_form.html", {"job": job})