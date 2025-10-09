
CareerHub is a Django-powered career platform designed to connect job seekers and recruiters. Built as a modular web app, it combines authentication, role-based dashboards, and integrated communication to simplify the hiring process.

🚀 Features (Current & Planned)
	•	Authentication & Role Management: Custom user model with Job Seeker and Recruiter roles.
	•	Role-Based Dashboards: Separate navigation and features for each type of user.
	•	Profile Onboarding: Guided setup for job seekers and recruiters after signup.
	•	Candidate Browsing (Recruiter Only): Recruiters can view a list of public candidate profiles.
	•	Candidate Profiles: Detailed job seeker information (skills, education, experience).
	•	Email Integration: Recruiters can contact candidates directly through the platform (via Gmail SMTP).
	•	Planned Features: Job search, application tracking, candidate pipelines, interactive maps for jobs, and admin extensions.

🛠️ Tech Stack
	•	Backend: Django (Python 3.13), SQLite
	•	Frontend: HTML, CSS, Bootstrap (with inline styling fallback)
	•	Email: Gmail SMTP with App Passwords
	•	Config: Environment variables managed via .env and python-dotenv
  
  Project Structure:
  CareerHub/
│── accounts/         # User authentication, profiles, role logic
│── home/             # Homepage and general views
│── templates/        # Shared templates
│── static/           # Static assets (CSS, JS, images)
│── CareerHub/        # Core settings, URLs, WSGI/ASGI config

👥 Team
	•	Joel Sari (Project Manager/ Lead Developer)
	•	Amrin
	•	Esther
	•	Srimayi
	•	Jacquelyn
  
