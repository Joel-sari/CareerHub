# jobs/urls.py
from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="job_list"),
    path("mine/", views.jobs_my_list, name="my_list"),
    path("new/", views.jobs_create, name="create"),
    path("<int:pk>/edit/", views.jobs_edit, name="edit"),
    path("<int:pk>/apply/", views.apply_to_job, name="apply_job"),
    path("<int:pk>/", views.job_detail, name="job_detail"),
    path("delete/<int:pk>/", views.delete_job, name="delete_job"),
    path("map/", views.job_map, name="job_map"),
    path("api/jobs-map/", views.jobs_map_api, name="jobs_map_api"),
]
