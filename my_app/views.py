from django.shortcuts import render, redirect
from . import models
import bcrypt
from .models import Classroom, ClassroomMembership
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .models import Classroom, Challenge

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

def join_classroom(request, slug):
    if not request.user.is_authenticated:
        messages.error(request, "You must log in to join a classroom.")
        return redirect("login")

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
        messages.error(request, "You must log in to leave a classroom.")
        return redirect("login")

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

# Showing How many members in details 

def classroom_detail(request, slug):
    classroom = Classroom.objects.annotate(
        members=Count('memberships')
    ).get(slug=slug)

    return render(request, "classrooms/detail.html", {"classroom": classroom})

# showing how many classrooms did the user joined 
def dashboard(request):
    user_classes_count = request.user.user_joined_classes.count()

    return render(request, "dashboard.html", {
        "user_classes_count": user_classes_count
    })

#ordering classrooms based on how many members joined 
def popular_classrooms(request):
    popular_classes = Classroom.objects.annotate(
        members=Count('memberships')
    ).order_by('-members')

    return render(request, "classrooms/popular.html", {
        "popular_classes": popular_classes
    })

#Implementing challenge-classroom assignment logic

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
            input_format=request.POST.get("input_format", ""),
            output_format=request.POST.get("output_format", ""),
            sample_io=request.POST.get("sample_io", "")
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

