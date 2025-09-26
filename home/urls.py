from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path("recruiter/jobs/", views.jobs_my_list, name="jobs_my_list"),
    path("recruiter/jobs/new/", views.jobs_create, name="jobs_create"),
    path("recruiter/jobs/<int:pk>/edit/", views.jobs_edit, name="jobs_edit"),
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),
    path("jobs/<int:pk>/apply/", views.apply_to_job, name="apply_job"),
    path("jobs/", views.job_list, name="job_list"),
]