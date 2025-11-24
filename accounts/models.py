from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


# -------------------------------------------------------
# Custom User model
# -------------------------------------------------------
class User(AbstractUser):
    JOB_SEEKER = 'job_seeker'
    RECRUITER = 'recruiter'

    ROLE_CHOICES = (
        (JOB_SEEKER, 'Job Seeker'),
        (RECRUITER, 'Recruiter'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_admin = models.BooleanField(default=False)


# -------------------------------------------------------
# Job Seeker Profile (now with profile picture)
# -------------------------------------------------------
class JobSeekerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jobseeker'
    )

    full_name = models.CharField(max_length=255, blank=True)   
    
    profile_picture = models.ImageField(upload_to="profile_pics/", null=True, blank=True)

    headline = models.CharField(max_length=255, blank=True)
    skills = models.TextField(blank=True)

    # These two will later be replaced by the structured models below
    education = models.TextField(blank=True)
    work_experience = models.TextField(blank=True)

    # Address fields
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    is_public = models.BooleanField(default=True)

    def __str__(self):
        return f"JobSeekerProfile({self.user.username})"


# -------------------------------------------------------
# Recruiter Profile (now with profile picture)
# -------------------------------------------------------
class RecruiterProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recruiter'
    )

    profile_picture = models.ImageField(upload_to="profile_pics/", null=True, blank=True)

    company_name = models.CharField(max_length=255, blank=True)
    position = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"RecruiterProfile({self.user.username})"


# -------------------------------------------------------
# NEW: Education Model (Multiple entries per user)
# -------------------------------------------------------
class Education(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="educations"
    )

    school = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    major = models.CharField(max_length=255, blank=True)

    start_year = models.IntegerField(null=True, blank=True)
    end_year = models.IntegerField(null=True, blank=True)
    currently_studying = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.school} – {self.degree}"


# -------------------------------------------------------
# NEW: Experience Model (Multiple entries per user)
# -------------------------------------------------------
class Experience(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="experiences"
    )

    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    currently_working = models.BooleanField(default=False)

    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} @ {self.company}"


# -------------------------------------------------------
# Candidate Saved Search (unchanged)
# -------------------------------------------------------
class CandidateSavedSearch(models.Model):
    VISIBILITY_PRIVATE = "private"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_saved_searches",
    )
    name = models.CharField(max_length=255)
    filters = models.JSONField()
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


# -------------------------------------------------------
# Signals: Auto-create profile on user signup
# -------------------------------------------------------
@receiver(post_save, sender=User)
def create_role_profile(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.role == User.JOB_SEEKER:
        JobSeekerProfile.objects.create(user=instance)
    elif instance.role == User.RECRUITER:
        RecruiterProfile.objects.create(user=instance)
