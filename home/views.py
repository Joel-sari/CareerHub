from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from accounts.models import User
from .models import Job, Application
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

# Public detail (so candidates can view/apply later)
def jobs_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    return render(request, "jobs/job_detail.html", {"job": job})

def home(request):
    return render(request, 'home/home.html')

@login_required
def apply_to_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.user.role != User.JOB_SEEKER:
        return redirect('home')
    if request.method == 'POST':
        note = request.POST.get('note', '')
        Application.objects.create(job=job, applicant=request.user, note=note)
        return redirect('jobseeker_dashboard')
    return render(request, 'jobs/apply_form.html', {'job': job})

def job_list(request):
    # Show all active jobs to everyone (or just job seekers)
    jobs = Job.objects.filter(is_active=True)
    return render(request, 'jobs/job_list.html', {'jobs': jobs})

def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    return render(request, 'jobs/job_detail.html', {'job': job})
