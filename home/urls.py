from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("recruiter/jobs/", views.jobs_my_list, name="jobs_my_list"),
    path("recruiter/jobs/new/", views.jobs_create, name="jobs_create"),
    path("recruiter/jobs/<int:pk>/edit/", views.jobs_edit, name="jobs_edit"),
    path("jobs/<int:pk>/", views.jobs_detail, name="jobs_detail"),
]