from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# -------------------------------------------------------
# Custom User model
# -------------------------------------------------------
# Why? Because we want to extend the default Django user 
# to support different roles (Job Seeker and Recruiter).
# This lets us branch features later depending on the role.
# This is where inheritamce comes to play!!!
# -------------------------------------------------------
class User(AbstractUser):
    JOB_SEEKER = 'job_seeker'
    RECRUITER = 'recruiter'

    ROLE_CHOICES = (
        (JOB_SEEKER, 'Job Seeker'),
        (RECRUITER, 'Recruiter'),
    )

    # New field: role
    # - Determines if the user is a job seeker or recruiter.
    # - Required for role-based dashboards and features.
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # is_admin marks whether the user has admin privileges
    is_admin = models.BooleanField(default=False)


# -------------------------------------------------------
# Job Seeker Profile
# -------------------------------------------------------
# Extends a User with job-seeker-specific fields.
# This keeps role-specific data separate and avoids 
# polluting the main User table with extra fields.
# -------------------------------------------------------
class JobSeekerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jobseeker'
    )
    headline = models.CharField(max_length=255, blank=True)
    skills = models.TextField(blank=True)
    education = models.TextField(blank=True)
    work_experience = models.TextField(blank=True)
    # New Address Fields (Needed for User Story 11)
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Privacy option: job seeker can hide their profile
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return f"JobSeekerProfile({self.user.username})"


# -------------------------------------------------------
# Recruiter Profile
# -------------------------------------------------------
# Extends a User with recruiter-specific fields.
# Useful for adding company info later on.
# -------------------------------------------------------
class RecruiterProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recruiter'
    )
    company_name = models.CharField(max_length=255, blank=True)
    position = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"RecruiterProfile({self.user.username})"


# -------------------------------------------------------
# Signal: Automatically create profile after user is created
# -------------------------------------------------------
# Why? When a new user signs up, we want to immediately
# give them the correct profile (JobSeekerProfile OR RecruiterProfile).
# This means we never have a user without a profile row.
# -------------------------------------------------------
@receiver(post_save, sender=User)
def create_role_profile(sender, instance, created, **kwargs):
    if not created:
        return  # only run the first time a user is created

    if instance.role == User.JOB_SEEKER:
        JobSeekerProfile.objects.create(user=instance)
    elif instance.role == User.RECRUITER:
        RecruiterProfile.objects.create(user=instance)

class CandidateSavedSearch(models.Model):
    VISIBILITY_PRIVATE = "private"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_saved_searches",
    )
    name = models.CharField(max_length=255)

    # Exact filter values at the moment of saving
    filters = models.JSONField()

    # Remember sort order if/when you add it later
    sort_order = models.CharField(max_length=100, blank=True)

    visibility = models.CharField(
        max_length=20,
        choices=[(VISIBILITY_PRIVATE, "Private")],
        default=VISIBILITY_PRIVATE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_run_at", "-updated_at", "-created_at"]

    def __str__(self):
        return f"{self.name} ({self.owner})"