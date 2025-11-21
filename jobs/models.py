from django.db import models
from django.conf import settings
from django.urls import reverse
import requests
import urllib.parse

class Job(models.Model):
    # ==============================
    # Employment Type Choices
    # ==============================
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

    # ==============================
    # Core Job Information
    # ==============================
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jobs_posted"
    )
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)

    # ==============================
    # Detailed Address Fields
    # ==============================
    # Each field corresponds to part of a real address.
    # This structure allows more accurate geocoding and cleaner input.
    street_address = models.CharField(max_length=255, blank=True, help_text="e.g. 123 Main Street")
    city = models.CharField(max_length=100, blank=True, help_text="e.g. Atlanta")
    state = models.CharField(max_length=100, blank=True, help_text="e.g. Georgia")
    zip_code = models.CharField(max_length=20, blank=True, help_text="e.g. 30332")
    country = models.CharField(max_length=100, blank=True, help_text="e.g. USA")

    # “location” stays as a single display-friendly field
    # It will be automatically populated from the above fields.
    location = models.CharField(max_length=255, blank=True, help_text="Auto-filled full address")

    # Coordinates for Google Maps
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # ==============================
    # Additional Job Info
    # ==============================
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default=FULL_TIME)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    min_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remote = models.BooleanField(default=False, help_text="True if this job can be done remotely")
    visa_sponsorship = models.BooleanField(default=False, help_text="True if this job offers visa sponsorship")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    
    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} @ {self.company or '—'}"

    def get_absolute_url(self):
        """Used for redirects after job creation."""
        return reverse("jobs:job_detail", args=[self.pk])

    # ==============================
    # Google Maps Geocoding
    # ==============================
    def geocode_address(self, address):
        """
        Convert a human‑readable address into latitude/longitude using
        Google Maps Geocoding API, with a **fallback** strategy for
        tricky/ambiguous addresses.

        Strategy:
        1) Try the full address as-is.
        2) If that fails, retry with a **simplified** query composed of the
           last two comma-separated parts (e.g., "City, State"), which
           often succeeds when street-level data is incomplete or uses
           abbreviations like "Rd" vs "Road".
        """
        # --- 1) First attempt: full address ---
        encoded = urllib.parse.quote(address.strip())
        url = (
            f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded}"
            f"&key={settings.GOOGLE_MAPS_API_KEY}"
        )
        resp = requests.get(url).json()

        if resp.get("status") == "OK" and resp.get("results"):
            loc = resp["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]

        # --- 2) Fallback attempt: try a simplified query ---
        # Example: "4 Birch Rd, New Milford, CT, 06776, USA" -> "New Milford, CT"
        parts = [p.strip() for p in address.split(",") if p.strip()]
        if len(parts) >= 2:
            simplified = ", ".join(parts[-2:])
            encoded_simple = urllib.parse.quote(simplified)
            retry_url = (
                f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_simple}"
                f"&key={settings.GOOGLE_MAPS_API_KEY}"
            )
            retry_resp = requests.get(retry_url).json()
            if retry_resp.get("status") == "OK" and retry_resp.get("results"):
                loc = retry_resp["results"][0]["geometry"]["location"]
                return loc["lat"], loc["lng"]

        # Nothing worked
        return None, None

    # ==============================
    # Save Override
    # ==============================
    def save(self, *args, **kwargs):
        """
        Override Django's save() to:
        - Normalize each address component (strip extra whitespace).
        - Build a clean, display-friendly `location` string from parts.
        - Geocode to fill `latitude`/`longitude` when missing *or* when
          any address component changes.
        """
        # --- Normalize address fields to reduce geocoding failures ---
        def _clean(s):
            return (s or "").strip().replace("  ", " ")

        self.street_address = _clean(self.street_address)
        self.city           = _clean(self.city)
        self.state          = _clean(self.state)
        self.zip_code       = _clean(self.zip_code)
        self.country        = _clean(self.country)

        # Build full address (omit blanks, keep natural commas)
        parts = [
            self.street_address,
            self.city,
            self.state,
            self.zip_code,
            self.country,
        ]
        full_address = ", ".join(p for p in parts if p)

        # Keep a copy to detect if address changed
        old_location = getattr(self, "location", "").strip()

        # Always update the human-readable `location` if we have parts
        if full_address:
            self.location = full_address
        else:
            # If recruiters typed a free-form `location`, keep it as-is
            self.location = _clean(self.location)

        # Decide whether we should (re)geocode
        must_geocode = False
        if (not self.latitude) or (not self.longitude):
            must_geocode = True
        elif self.location and old_location and self.location != old_location:
            # Address changed: refresh coordinates
            must_geocode = True

        # Perform geocoding if needed
        if must_geocode and self.location:
            lat, lng = self.geocode_address(self.location)
            if lat is not None and lng is not None:
                self.latitude = lat
                self.longitude = lng
        # Save record normally
        super().save(*args, **kwargs)


# ==============================
# Job Application Model
# ==============================
class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    note = models.TextField(blank=True)

    # Column status – controls which list (Backlog / Review / Closed)
    status = models.CharField(
        max_length=20,
        choices=[
            ("applied", "Applied"),
            ("review", "Under Review"),
            ("interview", "Interview"),  # optional
            ("closed", "Closed"),
        ],
        default="applied",
    )

    # FINAL decision – Hire or Reject (only when in Closed column)
    final_decision = models.CharField(
        max_length=10,
        choices=[
            ("none", "None"),
            ("hired", "Hired"),
            ("rejected", "Rejected"),
        ],
        default="none",
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "applicant")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.applicant} → {self.job}"
