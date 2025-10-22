# jobs/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.conf import settings
import math

# If your team keeps models in CareerHub.models, make sure jobs/models.py re-exports them:
# from CareerHub.models import Job, Application
# Otherwise, just import from the local app:
from .models import Job, Application

from accounts.models import User
from .forms import JobForm
from .decorators import recruiter_required

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points 
    on the Earth's surface (in miles) using the Haversine formula.
    
    The Haversine formula accounts for Earth's curvature — making it
    more accurate than a simple straight-line (Euclidean) distance.
    
    Parameters:
        lat1, lon1: Latitude and Longitude of the first point (in decimal degrees)
        lat2, lon2: Latitude and Longitude of the second point (in decimal degrees)
    
    Returns:
        The distance between the two coordinates in miles.
    """

    # Earth's radius (in miles)
    # Use 6371 for kilometers instead, depending on use case.
    R = 3958.8  

    # Convert all coordinates from degrees to radians.
    # Math trigonometric functions in Python use radians, not degrees.
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Calculate the difference (delta) in latitude and longitude.
    # This gives us how far apart the two points are on each axis.
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # ------------------------------
    # Haversine formula core steps:
    # ------------------------------
    # Step 1: Compute the "a" value (half-chord length between points)
    #         Using trigonometric sine and cosine to model Earth's curvature.
    a = (
        math.sin(dlat / 2) ** 2  # square of half the latitude difference
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )

    # Step 2: Compute the "c" value (angular distance in radians)
    #         2 * arcsin of the square root of a gives the central angle.
    c = 2 * math.asin(math.sqrt(a))

    # Step 3: Multiply the central angle by Earth's radius to get distance.
    distance = R * c

    # Return the computed distance in miles.
    return distance

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
    View to handle deletion of a job post by its recruiter.

    Steps:
    1. Require user to be logged in.
    2. Retrieve the Job object by primary key (pk) or return 404 if not found.
    3. Check if the current user is the recruiter who posted the job.
       If not, raise PermissionDenied to prevent unauthorized deletion.
    4. If the request method is POST, delete the job and redirect to the user's job list.
    5. If the request method is not POST, render a confirmation page asking the recruiter to confirm deletion.
    """
    # Retrieve the job or return 404 if it doesn't exist
    job = get_object_or_404(Job, pk=pk)

    # Ensure the current user is the recruiter who created the job
    if job.recruiter != request.user:
        raise PermissionDenied("You do not have permission to delete this job.")

    if request.method == "POST":
        # User confirmed deletion, so delete the job from the database
        job.delete()
        # Redirect to the list of jobs posted by the recruiter after deletion
        return redirect("jobs:my_list")

    # If not POST, render a confirmation page before deletion
    return render(request, "jobs/job_confirm_delete.html", {"job": job})

@login_required
@recruiter_required
def jobs_my_list(request):
    jobs = Job.objects.filter(recruiter=request.user)
    return render(request, "jobs/job_list_mine.html", {"jobs": jobs, "title": "My Job Posts"})

def job_list(request):
    # --- BASE QUERYSET ---
    # Get all active jobs, sorted from newest to oldest.
    all_jobs_qs = Job.objects.filter(is_active=True).order_by('-created_at')

    # --- GET JOBS USER HAS ALREADY APPLIED TO ---
    # Used later to display “✓ Already Applied” or disable apply button.
    applied_ids = set()
    if request.user.is_authenticated and getattr(request.user, "role", None) == User.JOB_SEEKER:
        applied_ids = set(
            Application.objects.filter(applicant=request.user).values_list('job_id', flat=True)
        )

    # --- HANDLE LOCATION & RADIUS PARAMETERS ---
    # Pull latitude, longitude, and radius from the query string.
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = float(request.GET.get("radius") or 10)  # Default to 10 miles if none is provided.

    nearby_jobs = []  # Will hold all nearby jobs within the radius.

    # --- CALCULATE DISTANCES USING HAVERSINE ---
    if lat and lng:  # Only run this block if coordinates are provided.
        try:
            user_lat = float(lat)
            user_lng = float(lng)

            # Filter out jobs that don’t have coordinates (to prevent errors).
            jobs_with_coords = all_jobs_qs.exclude(latitude__isnull=True, longitude__isnull=True)

            # Iterate through all jobs and calculate the distance from the user.
            for job in jobs_with_coords:
                dist = haversine_distance(user_lat, user_lng, job.latitude, job.longitude)

                # If the job is within the selected radius, include it in nearby_jobs.
                if dist <= radius:
                    job.distance_miles = round(dist, 1)  # Round for cleaner display (e.g., “5.3 mi”)
                    job.applied = job.id in applied_ids  # Mark if user already applied
                    nearby_jobs.append(job)

            # Sort nearby jobs by ascending distance (closest first).
            nearby_jobs.sort(key=lambda j: j.distance_miles)

        except ValueError:
            # If lat/lng were invalid (e.g., malformed query), skip the filter.
            pass

    # --- PREPARE “ALL JOBS” SECTION ---
    # Avoid showing the same job twice by excluding ones already shown in nearby_jobs.
    nearby_ids = {j.id for j in nearby_jobs}
    all_jobs = []

    for job in all_jobs_qs:
        if job.id in nearby_ids:
            continue  # Skip jobs already listed in “Jobs Near Me”
        job.applied = job.id in applied_ids
        all_jobs.append(job)

    # --- RENDER TEMPLATE ---
    # Pass both nearby_jobs and all_jobs to the HTML for rendering.
    return render(request, "jobs/job_list.html", {
        "nearby_jobs": nearby_jobs,
        "all_jobs": all_jobs,
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,  # <-- add this
    })

def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)

    applied = False
    if request.user.is_authenticated and getattr(request.user, "role", None) == User.JOB_SEEKER:
        applied = Application.objects.filter(job=job, applicant=request.user).exists()

    return render(request, "jobs/job_detail.html", {
        "job": job,
        "applied": applied,
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY, # <-- ADDED KEY HERE
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