from django.shortcuts import render
from django.http import HttpResponse

# Home page
def home(request):
    return render(request, 'home/home.html')

# Login placeholder
def login_view(request):
    return HttpResponse("Login page placeholder")

# Register placeholder
def register_view(request):
    return HttpResponse("Register page placeholder")
