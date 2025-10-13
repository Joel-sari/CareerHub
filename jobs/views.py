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
    return render(request, "jobs/job_list.html", {"jobs": jobs})

def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    return render(request, "jobs/job_detail.html", {"job": job})

@login_required
def apply_to_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.user.role != User.JOB_SEEKER:
        # you can also raise PermissionDenied, but redirect keeps UX smooth
        return redirect("home:home")
    if request.method == "POST":
        note = request.POST.get("note", "")
        Application.objects.create(job=job, applicant=request.user, note=note)
        return redirect("jobseeker_dashboard")  # assuming this exists in accounts
    return render(request, "jobs/apply_form.html", {"job": job})