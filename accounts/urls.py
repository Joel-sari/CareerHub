from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    # ---------------------------------------------------
    # AUTH ROUTES
    # ---------------------------------------------------
    # User registration (sign up with role selection)
    path("signup/", views.signup_view, name="signup"),

    # User login (redirects to role-specific dashboard)
    path("login/", views.CustomLoginView.as_view(), name="login"),

    # User logout (redirects back to home page)
    path("logout/", LogoutView.as_view(next_page="home"), name="logout"),


    # ---------------------------------------------------
    # DASHBOARDS
    # ---------------------------------------------------
    # Job Seeker dashboard → shown after login/onboarding
    path("dashboard/jobseeker/", views.jobseeker_dashboard, name="jobseeker_dashboard"),

    # Recruiter dashboard → shown after login/onboarding
    path("dashboard/recruiter/", views.recruiter_dashboard, name="recruiter_dashboard"),

    # Recruiter manage applicant kanban page
    path("dashboard/recruiter/manage_applicants", views.recruiter_applicants_kanban, name="applicant_kanban"),
    path("recruiter/applicant/<int:app_id>/update-status/", views.update_application_status, name="update_application_status"),

    # ---------------------------------------------------
    # PLACEHOLDER ROUTES (for future features)
    # ---------------------------------------------------
    # Recruiter features
    path("recruiter/post-job/", views.post_job_placeholder, name="post_job"),  # TODO: implement view
    path("recruiter/view-candidates/", views.view_candidates_placeholder, name="view_candidates"),  # TODO: implement view

    # Job Seeker features
    path("jobseeker/search-jobs/", views.search_jobs_placeholder, name="search_jobs"),  # TODO: implement view

    path("applicants_recruiter_view/", views.recruiter_applicants_kanban, name="applicant_kanban"),

    # ---------------------------------------------------
    # ONBOARDING ROUTES
    # ---------------------------------------------------
    # After signup, Job Seekers complete their profile
    path("onboarding/jobseeker/", views.jobseeker_onboarding, name="jobseeker_onboarding"),

    # After signup, Recruiters complete their profile
    path("onboarding/recruiter/", views.recruiter_onboarding, name="recruiter_onboarding"),


    # Candidate browsing & emailing
    path("candidates/", views.candidate_list, name="candidate_list"),
    path("candidates/<int:user_id>/", views.candidate_profile, name="candidate_profile"),
    path("candidates/<int:user_id>/email/", views.email_candidate, name="email_candidate"),

    # ---------------------------------------------------
    # ADMIN ROUTES
    # ---------------------------------------------------
    path("admin/users/", views.admin_user_list, name="admin_user_list"),
    path("admin/export-users-csv/", views.export_users_csv, name="export_users_csv"),


    path("applications/", views.my_applications, name="my_applications"),

]