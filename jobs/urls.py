# jobs/urls.py
from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="job_list"),
    path("<int:pk>/", views.job_detail, name="job_detail"),
    path("mine/", views.jobs_my_list, name="my_list"),
    path("new/", views.jobs_create, name="create"),
    path("<int:pk>/edit/", views.jobs_edit, name="edit"),
    path("<int:pk>/apply/", views.apply_to_job, name="apply_job"),
]
