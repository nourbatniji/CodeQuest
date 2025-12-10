from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from . import models
from .models import Classroom, ClassroomMembership, Challenge, Tag, Profile, Submission
from django.contrib import messages
from django.db.models import Count, Q, Sum
from .decorators import staff_or_superuser_required
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.utils import timezone
from datetime import timedelta
from django.views import View
from django.core.paginator import Paginator
from .models import Comment


def index(request):
    return render(request, 'index.html')

#  SIGNUP 
def signup(request):
    if request.method == 'POST':
        errors = models.validate_signup(request.POST)
        if errors:
            return render(request, 'signup.html', {'errors': errors})

        user = models.create_user(request.POST)
        Profile.objects.create(user=user)
        auth_login(request, user)

        return redirect('/dashboard')

    return render(request, 'signup.html')

#  LOGIN 
def login(request):
    if request.method == 'POST':
        errors = models.validate_login(request.POST)

        if errors:
            request.session['is_logged'] = False
            return render(request, 'login.html', {'errors': errors})

        user = models.authenticate_user(
            request.POST['email'], 
            request.POST['password']
        )
        
        if user:
            auth_login(request, user)
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



# =====================================================
#                NEW LEADERBOARD ENGINE
# =====================================================

def _compute_leaderboard(timeframe='all', classroom_id=None, limit=100):
    now = timezone.now()
    submissions = Submission.objects.filter(status='passed')

    # Time Filter
    if timeframe == 'week':
        submissions = submissions.filter(created_at__gte=now - timedelta(days=7))
    elif timeframe == 'month':
        submissions = submissions.filter(created_at__gte=now - timedelta(days=30))

    # Classroom Filter
    if classroom_id:
        submissions = submissions.filter(challenge__classroom_id=classroom_id)

    # Aggregation
    aggregated = (
        submissions
        .values('user', 'user__username')
        .annotate(total=Sum('points_awarded'))
        .order_by('-total')[:limit]
    )

    # Fetch profiles
    user_ids = [row['user'] for row in aggregated]
    profiles = Profile.objects.filter(user_id__in=user_ids)
    profile_map = {p.user_id: p for p in profiles}

    # Final structured list
    leaderboard = []
    for index, row in enumerate(aggregated, start=1):
        leaderboard.append({
            'rank': index,
            'user_id': row['user'],
            'username': row.get('user__username'),
            'total': row.get('total', 0),
            'profile': profile_map.get(row['user'])
        })

    return leaderboard



def leaderboard_page(request):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')

    timeframe = request.GET.get('time', 'all')  # all, week, month
    classroom_param = request.GET.get('classroom')

    try:
        classroom_id = int(classroom_param) if classroom_param is not None and classroom_param != 'all' else None
    except (TypeError, ValueError):
        classroom_id = None

    cache_key = f"leaderboard_{timeframe}_{classroom_id if classroom_id else 'all'}"
    leaderboard = cache.get(cache_key)

    if leaderboard is None:
        leaderboard = _compute_leaderboard(timeframe=timeframe, classroom_id=classroom_id, limit=200)
        cache.set(cache_key, leaderboard, timeout=300)  

    user_rank = None
    for entry in leaderboard:
        if entry.get('user_id') == request.user.id:
            user_rank = entry.get('rank')
            break

    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)
    user_points = request.user.profile.points

    selected_classroom = classroom_id
    selected_sort = request.GET.get('sort', 'points')

    context = {
        'leaderboard': leaderboard,
        'user_rank': user_rank,
        'user_points': user_points,
        'selected_time': timeframe,
        'selected_classroom': selected_classroom,
        'selected_sort': selected_sort,
        'classrooms': Classroom.objects.all(),
    }

    return render(request, 'leaderboard.html', context)





def profile_page(request):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    return render(request, 'profile.html')

@staff_or_superuser_required
def mentor_dashboard(request):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    return render(request, 'mentor.html')


# ------------- CLASSROOMS -------------
def classrooms_page(request):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    
    classrooms = Classroom.objects.annotate(
        members_count=Count('memberships')
    )
    return render(request, 'classrooms.html', {'classrooms': classrooms})


def classroom_detail(request, slug=None):
    if not request.user.is_authenticated:
        return render(request, 'not_found.html')
    
    classroom = get_object_or_404(
        Classroom.objects.annotate(members_count=Count('memberships')),
        slug=slug
    )

    is_member = ClassroomMembership.objects.filter(
        user=request.user,
        classroom=classroom
    ).exists()

    challenges_count = classroom.challenges.count()

    context = {
        "classroom": classroom,
        "is_member": is_member,
        "challenges_count": challenges_count,
    }
    return render(request, "classroom_details.html", context) 


def join_classroom(request, slug):
    if not request.user.is_authenticated:
        return render(request,"not_found.html")

    classroom = get_object_or_404(Classroom, slug=slug)

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

    try:
        classroom_id = int(classroom_id)
    except:
        classroom_id = None

    try:
        tag_id = int(tag_id)
    except:
        tag_id = None

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

class AddCommentView(View):
    def post(self, request, challenge_id, challenge_slug):
        if not request.user.is_authenticated:
            return redirect('login')

        challenge = get_object_or_404(Challenge, id=challenge_id, slug=challenge_slug)

        text = request.POST.get("text")
        parent_id = request.POST.get("parent_id")  # reply

        if not text.strip():
            return redirect(request.META.get("HTTP_REFERER"))

        parent = None
        if parent_id:
            parent = Comment.objects.filter(id=parent_id).first()

        Comment.objects.create(
            challenge=challenge,
            user=request.user,
            text=text,
            parent=parent
        )

        return redirect('challenge_detail', challenge_id=challenge.id, challenge_slug=challenge.slug)
    

class ChallengeDetailView(View):
    def get(self, request, challenge_id, challenge_slug):
        if not request.user.is_authenticated:
            return render(request, 'not_found.html')

        challenge = get_object_or_404(Challenge, id=challenge_id, slug=challenge_slug)

        #submissions
        submissions = challenge.submissions.filter(user=request.user).order_by('-created_at')

        #(parent is null)
        root_comments = challenge.comments.filter(parent__isnull=True).order_by('-created_at')

        # Pagination (5 comments per page)
        paginator = Paginator(root_comments, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            "challenge": challenge,
            "submissions": submissions,
            "page_obj": page_obj,    
        }
        return render(request, 'challenges/challenge_details.html', context)
