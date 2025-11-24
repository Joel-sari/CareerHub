from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    # ---------------------------------------------------
    # AUTH ROUTES
    # ---------------------------------------------------
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="home"), name="logout"),


    # ---------------------------------------------------
    # DASHBOARDS
    # ---------------------------------------------------
    path("dashboard/jobseeker/", views.jobseeker_dashboard, name="jobseeker_dashboard"),
    path("dashboard/recruiter/", views.recruiter_dashboard, name="recruiter_dashboard"),

    # Applicants Kanban board (recruiter)
    path("dashboard/recruiter/manage_applicants/",
         views.recruiter_applicants_kanban,
         name="applicant_kanban"),

    # Update applicant status
    path(
        "recruiter/applicant/<int:app_id>/update-status/",
        views.update_applicant_status,
        name="update_application_status"
    ),


    # ---------------------------------------------------
    # PLACEHOLDER ROUTES
    # ---------------------------------------------------
    path("recruiter/post-job/", views.post_job_placeholder, name="post_job"),
    path("recruiter/view-candidates/", views.view_candidates_placeholder, name="view_candidates"),
    path("jobseeker/search-jobs/", views.search_jobs_placeholder, name="search_jobs"),


    # ---------------------------------------------------
    # ONBOARDING & PROFILE EDIT ROUTES
    # ---------------------------------------------------
    path("onboarding/jobseeker/", views.jobseeker_onboarding, name="jobseeker_onboarding"),
    path("onboarding/recruiter/", views.recruiter_onboarding, name="recruiter_onboarding"),

    # NEW — Edit Job Seeker Profile
    path("jobseeker/edit/", views.jobseeker_edit_profile, name="jobseeker_edit_profile"),


    # ---------------------------------------------------
    # CANDIDATES (Recruiter only)
    # ---------------------------------------------------
    path("candidates/", views.candidate_list, name="candidate_list"),
    path("candidates/<int:user_id>/", views.candidate_profile, name="candidate_profile"),
    path("candidates/<int:user_id>/email/", views.email_candidate, name="email_candidate"),


    # ---------------------------------------------------
    # ADMIN ROUTES
    # ---------------------------------------------------
    path("admin/users/", views.admin_user_list, name="admin_user_list"),
    path("admin/export-users-csv/", views.export_users_csv, name="export_users_csv"),


    # ---------------------------------------------------
    # JOB SEEKER APPLICATIONS
    # ---------------------------------------------------
    path("applications/", views.my_applications, name="my_applications"),


    # ---------------------------------------------------
    # CANDIDATE SAVED SEARCH (Recruiter)
    # ---------------------------------------------------
    path("candidates/saved-searches/create/",
         views.create_candidate_saved_search,
         name="candidate_saved_search_create"),
    path("candidates/saved-searches/<int:pk>/rename/",
         views.rename_candidate_saved_search,
         name="candidate_saved_search_rename"),
    path("candidates/saved-searches/<int:pk>/update-from-current/",
         views.update_candidate_saved_search_from_current,
         name="candidate_saved_search_update_from_current"),
    path("candidates/saved-searches/<int:pk>/delete/",
         views.delete_candidate_saved_search,
         name="candidate_saved_search_delete"),
    path("candidates/saved-searches/<int:pk>/run/",
         views.run_candidate_saved_search,
         name="candidate_saved_search_run"),

    # Recruiter Preferences
    path("recruiter/preferences/", views.recruiter_preferences_view,name="recruiter_preferences",
)
]
