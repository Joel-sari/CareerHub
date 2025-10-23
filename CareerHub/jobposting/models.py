from django.db import models
from django.conf import settings


# Create your models here.

class Job(models.Model):
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posted_jobs"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    salary_range = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    note = models.TextField(blank=True)  # the tailored note
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

    def __str__(self):
        return f"{self.applicant} → {self.job}"