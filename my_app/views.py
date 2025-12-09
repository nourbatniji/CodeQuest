from django.shortcuts import render, redirect,get_object_or_404
from . import models
from .models import Classroom, ClassroomMembership, Challenge, Tag
from django.contrib import messages
from django.db.models import Count, Q
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


# ------------- CLASSROOMS -------------
def classrooms_page(request):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    
    classrooms = Classroom.objects.annotate( # adds extra calculated fields to each object in a queryset using database
        members_count=Count('memberships')
    )
    return render(request, 'classrooms.html', {'classrooms': classrooms})


def classroom_detail(request, slug=None):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    
    classroom = get_object_or_404(Classroom.objects.annotate(members_count=Count('memberships')), slug=slug) # looks for a classroom with the given slug/ find the classroom whose slug field matches the value in the URL

    is_member = ClassroomMembership.objects.filter(user=request.user, classroom=classroom).exists()

    challenges_count = classroom.challenges.count() if hasattr(classroom, "challenges") else 0 # if classroom has attribute named 'challenges'

    context = {
        "classroom": classroom,
        "is_member": is_member,
        "challenges_count": challenges_count,
    }
    return render(request, "classroom_details.html", context) 


def join_classroom(request, slug):
    if not request.user.is_authenticated:
        return render(request,"not_found.html")

    classroom = get_object_or_404(Classroom, slug=slug)# fetch the classroom by slug

    membership, created = ClassroomMembership.objects.get_or_create( # tries to find a row with this row and this classroom
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
        return render(request, "not_found.html")
    
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

    return redirect("classrooms_page")  


# ------------- CHALLENGES -------------
def challenge_list(request):
    challenges = Challenge.objects.all()
    tags = Tag.objects.all()
    classrooms = Classroom.objects.all()

    difficulty = request.GET.get("difficulty")
    classroom_id = request.GET.get("classroom")
    tag_id = request.GET.get("tag")

    if difficulty and difficulty != 'all':
        challenges = challenges.filter(difficulty__iexact=difficulty)

    if classroom_id:
        challenges = challenges.filter(classroom_id=classroom_id)

    if tag_id:
        challenges = challenges.filter(tags__id=tag_id)


    context = {
        'challenges': challenges,
        'classrooms': classrooms,
        'tags': tags,
        'selected_difficulty': difficulty,
        'selected_classroom': classroom_id,
        'selected_tag': tag_id
    }

    return render(request, "challenges.html", context)



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
