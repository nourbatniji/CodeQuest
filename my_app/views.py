from django.shortcuts import render, redirect,get_object_or_404
from django.db.models import Count, Q
from . import models
from .models import Classroom, ClassroomMembership
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .models import Classroom, Challenge
from .decorators import staff_or_superuser_required

from django.contrib.auth import login as auth_login, logout as auth_logout


def index(request):
    return render(request, 'index.html')

#  SIGNUP 
def signup(request):
    if request.method == 'POST':
        errors = models.validate_signup(request.POST)
        if errors: #check data format
            return render(request, 'signup.html', {'errors': errors})

        user = models.create_user(request.POST) # create user

        auth_login(request, user) # mark this user as logged in for this session

        return redirect('/dashboard')

    return render(request, 'signup.html')


#  LOGIN 
def login(request):
    if request.method == 'POST':
        errors = models.validate_login(request.POST)

        if errors: #check data format
            request.session['is_logged'] = False
            return render(request, 'login.html', {'errors': errors})

        user = models.authenticate_user( # does this email & password match a real account?
            request.POST['email'], 
            request.POST['password']
        )
        
        if user:
            auth_login(request, user) # mark this user as logged in for this session
            if user.is_staff:
                return redirect('/mentor_dashboard')
            else:
                return redirect('/dashboard')

          
        request.session['is_logged'] = False
        errors['incorrect_pw'] = 'Incorrect Password'
        return render(request, 'login.html', {'errors': errors})

    return render(request, 'login.html')


def signout(request):
    auth_logout(request)
    request.session.flush()
    return redirect('/')

def dashboard(request):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    context = {
        'user' : request.user,
        "user_classes_count" : request.user.user_joined_classes.count()
    }
    return render(request, 'dashboard.html', context)

def classrooms_page(request):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    return render(request, 'classrooms.html')



def challenges_page(request):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    challenges = models.Challenge.objects.annotate(
        solved_count=Count('submissions', filter=Q(submissions__status='passed'), distinct=True)
    )
    return render(request, 'challenges.html', {'challenges': challenges})

def challenge_detail(request,slug):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    challenge = get_object_or_404(models.Challenge, slug=slug)
    submissions = challenge.submissions.filter(user=request.user).order_by('-created_at')
    comments = challenge.comments.all().order_by('-created_at')
    context={"challenge": challenge,
            "submissions": submissions,
            "comments": comments}
    return render(request, 'challenge_details.html',context)

def leaderboard_page(request):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    return render(request, 'leaderboard.html')

def profile_page(request):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    return render(request, 'profile.html')

# wrapper runs before mentor-dashboard, is user logged?, is logged and superuser/staff? if yes run the next view
@staff_or_superuser_required
def mentor_dashboard(request):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    return render(request, 'mentor.html')

def join_classroom(request, slug):
    if not request.user.is_authenticated:
        return render(request,"not_found.html")

    classroom = get_object_or_404(Classroom, slug=slug)

    # Prevent duplicate membership
    membership, created = ClassroomMembership.objects.get_or_create(
        user=request.user,
        classroom=classroom
    )

    if created:
        messages.success(request, f"You joined {classroom.name}!")
    else:
        messages.info(request, "You are already a member of this classroom.")

    return redirect("classroom_detail", slug=slug)

def leave_classroom(request, slug):
    if not request.user.is_authenticated:
        return render("not_found.html")
    classroom = get_object_or_404(Classroom, slug=slug)

    membership = ClassroomMembership.objects.filter(
        user=request.user,
        classroom=classroom
    )

    if membership.exists():
        membership.delete()
        messages.success(request, f"You left {classroom.name}.")
    else:
        messages.info(request, "You are not a member of this classroom.")

    return redirect("dashboard")  # or wherever you want to redirect

#Showing how many members for each classroom
def classroom_list(request):
    classrooms = Classroom.objects.annotate(
        members=Count('memberships')
    )

    return render(request, "classrooms/list.html", {"classrooms": classrooms})

#method to get classroom by id or slug
def get_classroom(id=None, slug=None):
    queryset = Classroom.objects.annotate(members=Count('memberships'))  
    if id is not None:
        return get_object_or_404(queryset, id=id)
    elif slug is not None:
        return get_object_or_404(queryset, slug=slug)
    else:
        raise ValueError("You must provide either an id or a slug")
    
# Showing How many members in details
def classroom_detail(request, slug=None, classroom_id=None):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    classroom = get_classroom(id=classroom_id, slug=slug)
    return render(request, "classrooms/detail.html", {"classroom": classroom}) 

def classroom_detail(request,classroom_id):
    
    classroom = get_object_or_404(models.Classroom, id=classroom_id)
    return render(request, 'classroom_details.html', {'classroom': classroom})


#ordering classrooms based on how many members joined 
def popular_classrooms(request):
    popular_classes = Classroom.objects.annotate(
        members=Count('memberships')
    ).order_by('-members')

    return render(request, "classrooms/popular.html", {
        "popular_classes": popular_classes
    })

#Implementing challenge-classroom assignment logic
@staff_or_superuser_required
def create_challenge(request, classroom_slug):
    classroom = get_object_or_404(Classroom, slug=classroom_slug)

    # Only the mentor can create challenges
    if request.user != classroom.mentor:
        messages.error(request, "Only the mentor can create challenges.")
        return redirect("classroom_detail", slug=classroom_slug)

    if request.method == "POST":
        Challenge.objects.create(
            title=request.POST["title"],
            description=request.POST["description"],
            difficulty=request.POST["difficulty"],
            tags=request.POST.get("tags", ""),
            classroom=classroom,
            input_description=request.POST.get("input_format", ""),
            output_desciption=request.POST.get("output_format", ""),
            sample_input=request.POST.get("sample_io", "")
        )
        messages.success(request, "Challenge created successfully!")
        return redirect("classroom_detail", slug=classroom_slug)

    return render(request, "challenges/create.html", {"classroom": classroom})

#Add challenge filtering (difficulty/classroom/tags)

def challenge_list(request):
    challenges = Challenge.objects.all()

    difficulty = request.GET.get("difficulty")
    classroom_id = request.GET.get("classroom")
    tag = request.GET.get("tag")

    if difficulty:
        challenges = challenges.filter(difficulty=difficulty)

    if classroom_id:
        challenges = challenges.filter(classroom__id=classroom_id)

    if tag:
        challenges = challenges.filter(tags__icontains=tag)

    return render(request, "challenges/list.html", {
        "challenges": challenges
    })

