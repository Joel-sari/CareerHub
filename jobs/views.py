# jobs/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.db.models import Count
import math
import json

from .models import Job, Application
from accounts.models import User
from .forms import JobForm
from .decorators import recruiter_required
from accounts.models import JobSeekerProfile
from messaging.models import JobNotification


from django.http import JsonResponse, HttpResponseForbidden


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

        # ---------------------------------------------
        # NEW: Notify nearby job seekers about this job
        # ---------------------------------------------
        # Define "near" as same city + state + country
        if job.city and job.state and job.country:
            nearby_seekers = JobSeekerProfile.objects.filter(
                is_public=True,
                city__iexact=job.city,
                state__iexact=job.state,
                country__iexact=job.country,
            ).select_related("user")

            notifications = []
            for profile in nearby_seekers:
                if profile.user == request.user:
                    continue  # don't notify the posting recruiter
                text = f"New job near you: {job.title}"
                if job.company:
                    text += f" at {job.company}"
                if job.city:
                    text += f" in {job.city}"

                notifications.append(
                    JobNotification(
                        user=profile.user,
                        job=job,
                        text=text,
                    )
                )

            if notifications:
                # unique_together(user, job) will prevent duplicates over time
                JobNotification.objects.bulk_create(notifications, ignore_conflicts=True)

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

        # If this job was opened via a notification, mark that notification read
        notif_id = request.GET.get("notif_id")
        if notif_id:
            from messaging.models import JobNotification
            JobNotification.objects.filter(
                id=notif_id,
                user=request.user,
                job=job,
            ).update(is_read=True)

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
# Recruiter Map View (My Jobs + Applicant Counts)
# ===============================================================
@login_required
@recruiter_required
def recruiter_map(request):
    """
    Map for recruiters:
    - Mode 1: marker for each job posting
    - Mode 2: same markers but with applicant counts
    """
    user = request.user

    # 1) Jobs belonging to this recruiter that have coordinates
    jobs_qs = (
        Job.objects
        .filter(recruiter=user, is_active=True)
        .exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
    )

    # 2) Mode 1 data → plain job pins
    job_pins = [
        {
            "id": j.id,
            "title": j.title,
            "company": getattr(j, "company", ""),
            "location": getattr(j, "location", ""),
            "lat": float(j.latitude),
            "lng": float(j.longitude),
            "detailUrl": j.get_absolute_url() if hasattr(j, "get_absolute_url") else f"/jobs/{j.id}/",
        }
        for j in jobs_qs
    ]

    # 3) Mode 2 → same markers, but annotated with applicant counts
    jobs_with_counts = (
        jobs_qs
        .annotate(app_count=Count("applications"))   # <-- FIXED LINE
    )

    applicant_pins = [
        {
            "id": j.id,
            "title": j.title,
            "company": getattr(j, "company", ""),
            "location": getattr(j, "location", ""),
            "lat": float(j.latitude),
            "lng": float(j.longitude),
            "applicants": j.app_count,
            "detailUrl": j.get_absolute_url() if hasattr(j, "get_absolute_url") else f"/jobs/{j.id}/",
        }
        for j in jobs_with_counts
        if j.app_count > 0
    ]

    return render(request, "jobs/recruiter_map.html", {
        "jobs_json": json.dumps(job_pins),
        "applicants_json": json.dumps(applicant_pins),
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
    })


# ===============================================================
# Recruiter Map API (JSON for recruiter map)
# ===============================================================
@login_required
@recruiter_required
def recruiter_map_api(request):
    """
    JSON endpoint for the recruiter map.

    Optional query param:
      - mode=jobs        → basic job pins
      - mode=applicants  → same pins with applicant counts
    """
    user = request.user
    mode = request.GET.get("mode", "jobs")

    # Base queryset: this recruiter's active jobs with coordinates
    jobs_qs = (
        Job.objects
        .filter(recruiter=user, is_active=True)
        .exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
    )

    # If we need applicant counts, annotate first
    if mode == "applicants":
        jobs_qs = jobs_qs.annotate(app_count=Count("applications"))

    payload = []
    for j in jobs_qs:
        item = {
            "id": j.id,
            "title": j.title,
            "company": getattr(j, "company", ""),
            "location": getattr(j, "location", ""),
            "lat": float(j.latitude),
            "lng": float(j.longitude),
            "detailUrl": j.get_absolute_url() if hasattr(j, "get_absolute_url") else f"/jobs/{j.id}/",
        }
        if mode == "applicants":
            item["applicants"] = getattr(j, "app_count", 0)
        payload.append(item)

    return JsonResponse({"jobs": payload})



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


# ===============================================================
# Applicant View Kanban
# ===============================================================

@login_required
def recruiter_applicants_kanban(request):
    if request.user.role != User.RECRUITER:
        return HttpResponseForbidden("Only recruiters can view this page.")

    applications = Application.objects.filter(job__recruiter=request.user).select_related("applicant", "job")

    return render(request, "accounts/applicants_recruiter_view.html", {
        "applications": applications,
    })


@login_required
def update_application_status(request, app_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=400)

    app = get_object_or_404(Application, id=app_id)

    if app.job.recruiter != request.user:
        return JsonResponse({"error": "Not allowed"}, status=403)

    new_status = request.POST.get("status")

    if new_status not in ["applied", "under_review", "interview", "hired"]:
        return JsonResponse({"error": "Invalid status"}, status=400)

    app.status = new_status
    app.save()

    return JsonResponse({"success": True})
