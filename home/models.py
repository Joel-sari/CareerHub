from django.db import models
from django.conf import settings
from django.urls import reverse

class Job(models.Model):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT  = "contract"
    INTERN    = "intern"
    TEMP      = "temp"

    EMPLOYMENT_TYPES = [
        (FULL_TIME, "Full-time"),
        (PART_TIME, "Part-time"),
        (CONTRACT,  "Contract"),
        (INTERN,    "Internship"),
        (TEMP,      "Temporary"),
    ]

    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,              # important for swapped User
        on_delete=models.CASCADE,
        related_name="jobs_posted"
    )
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default=FULL_TIME)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    min_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} @ {self.company or '—'}"

    def get_absolute_url(self):
        return reverse("jobs_detail", args=[self.pk])
    
class Application(models.Model):
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    note = models.TextField(blank=True)  # the tailored note from the job seeker
    status = models.CharField(
        max_length=20,
        choices=[
            ("Applied", "Applied"),
            ("Review", "Under Review"),
            ("Interview", "Interview"),
            ("Hired", "Hired"),
            ("Closed", "Closed"),
        ],
        default="Applied",
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "applicant")  # prevent duplicate applications
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.applicant} → {self.job}"