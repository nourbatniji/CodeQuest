from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'index.html')

def login(request):
    return render(request, 'login.html')

def signup(request):
    return render(request, 'signup.html')


def dashboard(request):
    return render(request, 'dashboard.html')

def classrooms_page(request):
    return render(request, 'classrooms.html')

def challenges_page(request):
    return render(request, 'challenges.html')

def leaderboard_page(request):
    return render(request, 'leaderboard.html')

def profile_page(request):
    return render(request, 'profile.html')