# jobs/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.conf import settings
import math

from .models import Job, Application
from accounts.models import User
from .forms import JobForm
from .decorators import recruiter_required

from django.http import JsonResponse


# ===============================================================
# Haversine Distance Helper
# ===============================================================
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points 
    on the Earth's surface (in miles) using the Haversine formula.
    """
    R = 3958.8  # Earth’s radius in miles
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


# ===============================================================
# Recruiter CRUD Views
# ===============================================================
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
def delete_job(request, pk):
    """
    Allow recruiters to delete their job posts.
    """
    job = get_object_or_404(Job, pk=pk)
    if job.recruiter != request.user:
        raise PermissionDenied("You do not have permission to delete this job.")

    if request.method == "POST":
        job.delete()
        return redirect("jobs:my_list")

    return render(request, "jobs/job_confirm_delete.html", {"job": job})


@login_required
@recruiter_required
def jobs_my_list(request):
    """
    Show the list of jobs posted by the logged-in recruiter.
    """
    jobs = Job.objects.filter(recruiter=request.user).order_by('-created_at')
    return render(request, "jobs/job_list_mine.html", {
        "jobs": jobs,
        "title": "My Job Posts",
    })


# ===============================================================
# Job List (User Story 2 filters)
# ===============================================================
def job_list(request):
    # --- BASE QUERYSET ---
    all_jobs_qs = Job.objects.filter(is_active=True).order_by('-created_at')

    # --- FILTERING LOGIC (User Story 2) ---
    title = request.GET.get('title')
    skills = request.GET.get('skills')
    salary_min = request.GET.get('salary_min')
    salary_max = request.GET.get('salary_max')
    remote = request.GET.get('remote')
    visa = request.GET.get('visa')

    # Filter by title
    if title:
        all_jobs_qs = all_jobs_qs.filter(title__icontains=title.strip())

    # Filter by skills (search inside requirements)
    if skills:
        all_jobs_qs = all_jobs_qs.filter(requirements__icontains=skills.strip())

    # Filter by salary range
    if salary_min:
        all_jobs_qs = all_jobs_qs.filter(max_salary__gte=salary_min)
    if salary_max:
        all_jobs_qs = all_jobs_qs.filter(min_salary__lte=salary_max)

    # Filter by remote (case-insensitive)
    if remote is not None and remote != "":
        remote_val = str(remote).lower() in ['true', '1', 'yes']
        all_jobs_qs = all_jobs_qs.filter(remote=remote_val)

    # Filter by visa sponsorship (case-insensitive)
    if visa is not None and visa != "":
        visa_val = str(visa).lower() in ['true', '1', 'yes']
        all_jobs_qs = all_jobs_qs.filter(visa_sponsorship=visa_val)

    # --- APPLIED JOBS FOR CURRENT USER ---
    applied_ids = set()
    if request.user.is_authenticated and getattr(request.user, "role", None) == User.JOB_SEEKER:
        applied_ids = set(Application.objects.filter(applicant=request.user)
                          .values_list('job_id', flat=True))

    # --- LOCATION & RADIUS ---
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = float(request.GET.get("radius") or 10)

    nearby_jobs = []
    if lat and lng:
        try:
            user_lat = float(lat)
            user_lng = float(lng)
            jobs_with_coords = all_jobs_qs.exclude(latitude__isnull=True, longitude__isnull=True)

            for job in jobs_with_coords:
                dist = haversine_distance(user_lat, user_lng, job.latitude, job.longitude)
                if dist <= radius:
                    job.distance_miles = round(dist, 1)
                    job.applied = job.id in applied_ids
                    nearby_jobs.append(job)
            nearby_jobs.sort(key=lambda j: j.distance_miles)
        except ValueError:
            pass

    # --- PREPARE “ALL JOBS” SECTION ---
    nearby_ids = {j.id for j in nearby_jobs}
    all_jobs = []
    for job in all_jobs_qs:
        if job.id in nearby_ids:
            continue
        job.applied = job.id in applied_ids
        all_jobs.append(job)

    # --- RENDER ---
    return render(request, "jobs/job_list.html", {
        "nearby_jobs": nearby_jobs,
        "all_jobs": all_jobs,
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
    })


# ===============================================================
# Job Detail and Apply
# ===============================================================
def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    applied = False
    if request.user.is_authenticated and getattr(request.user, "role", None) == User.JOB_SEEKER:
        applied = Application.objects.filter(job=job, applicant=request.user).exists()
    return render(request, "jobs/job_detail.html", {
        "job": job,
        "applied": applied,
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
    })


@login_required
def apply_to_job(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)

    if getattr(request.user, "role", None) != User.JOB_SEEKER:
        raise PermissionDenied("Only job seekers can apply for jobs.")

    if Application.objects.filter(job=job, applicant=request.user).exists():
        return render(request, "jobs/apply_form.html", {
            "job": job,
            "error": "You have already applied for this job."
        })

    if request.method == "POST":
        note = request.POST.get("note", "").strip()
        Application.objects.create(job=job, applicant=request.user, note=note)
        return redirect("jobs:job_detail", pk=job.pk)

    return render(request, "jobs/apply_form.html", {"job": job})


# ===============================================================
# Job Map APIs
# ===============================================================
@login_required
def job_map(request):
    """Full-screen page with a world map and all job pins."""
    return render(request, "jobs/job_map.html", {
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
    })


@login_required
def jobs_map_api(request):
    """Lightweight JSON for pins on the all-jobs map."""
    qs = Job.objects.filter(is_active=True).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    data = [{
        "id": j.id,
        "title": j.title,
        "company": getattr(j, "company", ""),
        "location": getattr(j, "location", ""),
        "lat": float(j.latitude),
        "lng": float(j.longitude),
        "detailUrl": j.get_absolute_url() if hasattr(j, "get_absolute_url") else f"/jobs/{j.id}/",
    } for j in qs]
    return JsonResponse({"jobs": data})

# ===============================================================
# Job Seeker Dashboard
# ===============================================================
@login_required
def jobseeker_dashboard(request):
    """Displays personalized job recommendations and application status for the logged-in job seeker."""
    user = request.user

    # Restrict to job seekers only
    if getattr(user, "role", None) != User.JOB_SEEKER:
        raise PermissionDenied("Only job seekers can access this dashboard.")

    # Recent applications (latest 5)
    applications = (
        Application.objects
        .filter(applicant=user)
        .select_related("job")
        .order_by("-created_at")[:5]
    )

    # Simple recommendation: nearest jobs or recent active jobs
    recommended_jobs = Job.objects.filter(is_active=True).order_by("-created_at")[:3]

    # Optional: If you later store location in user profile, you can compute actual nearby jobs:
    # if user.profile.latitude and user.profile.longitude:
    #     recommended_jobs = Job.objects.filter(is_active=True)[:3]
    #     # (Apply haversine_distance filtering similar to job_list)

    context = {
        "user": user,
        "recommended_jobs": recommended_jobs,
        "applications": applications,
    }

    return render(request, "jobs/jobseeker_dashboard.html", context)
