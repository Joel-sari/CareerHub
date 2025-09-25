from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def home(request):
    return render(request, 'home/home.html')

def login_view(request):
    return HttpResponse("Login page placeholder")

def register_view(request):
    return HttpResponse("Register page placeholder")