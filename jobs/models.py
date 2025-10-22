from django.db import models
from django.conf import settings
from django.urls import reverse
import requests

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
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jobs_posted"
    )
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)

    #Essential for GOOGLE MAPS Integration
    location = models.CharField(max_length=200, blank=True)
    latitude= models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)


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
        return reverse("jobs:job_detail", args=[self.pk])
    
    # Geocoding Function
    def geocode_address(self, address):
        """
        Converts a human-readable address into latitude and longitude coordinates
        using the Google Maps Geocoding API.
        """
        # Construct the API request URL using the address and your API key from settings.py
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={settings.GOOGLE_MAPS_API_KEY}"

        # Send an HTTP GET request to Google’s API and parse the JSON response
        response = requests.get(url).json()

        # Check if Google successfully found a location for the given address 
        if response['status'] == 'OK':
            # Extract latitude and longitude from the first result in the response
            loc = response['results'][0]['geometry']['location']
            lat = loc['lat']
            lng = loc['lng']

            # Return coordinates as a tuple
            return lat, lng

        # If Google didn’t return a valid result, return None values
        return None, None
    
    # Overriding the Save Method
    # ============================
    def save(self, *args, **kwargs):
        """
        Overrides Django’s default save() method.
        Automatically fetches and saves latitude and longitude
        when a new job or location update occurs.
        """
        # Only attempt geocoding if the location field has a value
        # AND latitude/longitude have not been set yet.
        if self.location and (not self.latitude or not self.longitude):
            # Call the geocode function to get coordinates
            lat, lng = self.geocode_address(self.location)

            # If valid coordinates were returned, store them in the model
            if lat and lng:
                self.latitude = lat
                self.longitude = lng

        # Finally, call the parent save() method to actually store the record in the DB
        super().save(*args, **kwargs)

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
    note = models.TextField(blank=True)
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
        unique_together = ("job", "applicant")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.applicant} → {self.job}"