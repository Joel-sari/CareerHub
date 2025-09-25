from django.urls import path
from . import views



urlpatterns = [
    path('', views.home, name='home'),
    # Moved login and signup to accounts app.
]
