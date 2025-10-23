from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Job, Application

@login_required
def apply_to_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == "POST":
        note = request.POST.get("note", "")
        Application.objects.create(job=job, applicant=request.user, note=note)
        return redirect("application_success", job_id=job.id)

    # Optional: render a page with a form to add a note
    return render(request, "jobs/apply_form.html", {"job": job})