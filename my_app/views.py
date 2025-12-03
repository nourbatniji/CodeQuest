from django.shortcuts import render, redirect
from . import models
import bcrypt

def index(request):
    return render(request, 'index.html')

#  SIGNUP 
def signup(request):
    if request.method == 'POST':
        errors = models.validate_signup(request.POST)
        if errors:
            return render(request, 'signup.html', {'errors': errors})

        user = models.create_user(request.POST)
        request.session['user_id'] = user.id
        request.session['is_logged'] = True
        return redirect('/dashboard')

    return render(request, 'signup.html')


#  LOGIN 
def login(request):
    if request.method == 'POST':
        errors = models.validate_login(request.POST)
        user = models.get_user_by_email(request.POST['email'])

        if errors:
            request.session['is_logged'] = False
            return render(request, 'login.html', {'errors': errors})

        if user:
            logged_user = user[0]
            if bcrypt.checkpw(request.POST['password'].encode(), logged_user.password.encode()):
                request.session['user_id'] = logged_user.id
                request.session['is_logged'] = True
                return redirect('/dashboard')
            else:
                request.session['is_logged'] = False
                errors['incorrect_pw'] = 'Incorrect Password'
                return render(request, 'login.html', {'errors': errors})


        return render(request, 'login.html', {'errors': errors})


    return render(request, 'login.html')


def signout(request):
    request.session.flush()
    return redirect('/')

def dashboard(request):
    return render(request, 'dashboard.html')

def classrooms_page(request):
    return render(request, 'classrooms.html')

def classroom_detail(request, id):
    return render(request, 'classroom_details.html')

def challenges_page(request):
    return render(request, 'challenges.html')

def challenge_detail(request):
    return render(request, 'challenge_details.html')

def leaderboard_page(request):
    return render(request, 'leaderboard.html')

def profile_page(request):
    return render(request, 'profile.html')

def mentor_dashboard(request):
    return render(request, 'mentor.html')
