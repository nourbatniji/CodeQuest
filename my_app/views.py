from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from . import models
from .models import (
    Classroom,
    ClassroomMembership,
    Challenge,
    Tag,
    Profile,
    Submission,
    Comment,
)
from django.contrib import messages
from django.db.models import Count, Q, Sum
from .decorators import staff_or_superuser_required
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from django.views import View
from django.core.paginator import Paginator
import json
import traceback
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, "index.html")


# --------------- SIGNUP ---------------
def signup(request):
    if request.method == "POST":
        errors = models.validate_signup(request.POST)
        if errors:
            return render(request, "signup.html", {"errors": errors})

        user = models.create_user(request.POST)
        auth_login(request, user)

        return redirect("/dashboard")

    return render(request, "signup.html")



# --------------- LOGIN ---------------
def login(request):
    if request.method == "POST":
        errors = models.validate_login(request.POST)

        if errors:
            request.session["is_logged"] = False
            return render(request, "login.html", {"errors": errors})

        user = models.authenticate_user(
            request.POST["email"],
            request.POST["password"],
        )

        if user:
            auth_login(request, user)
            if user.is_staff:
                return redirect("/mentor_dashboard")
            else:
                return redirect("/dashboard")

        request.session["is_logged"] = False
        errors["incorrect_pw"] = "Incorrect Password"
        return render(request, "login.html", {"errors": errors})

    return render(request, "login.html")


def signout(request):
    auth_logout(request)
    request.session.flush()
    return redirect("/")

from django.db.models import Sum

@login_required
def dashboard(request):
    if not request.user.is_authenticated:
        return render(request, "not_found.html")

    total_solved = (
    Submission.objects.filter(
        user=request.user,
        status="passed",
    )
    .values("challenge")   # group by challenge
    .distinct()            # remove duplicates
    .count()               # count unique challenges
)

    # total points from passed submissions
    total_points = (
        Submission.objects.filter(user=request.user, status="passed")
        .aggregate(Sum("points_awarded"))["points_awarded__sum"]
        or 0
    )

    # classrooms the user joined
    my_classrooms = (
        Classroom.objects.filter(memberships__user=request.user)
        .annotate(
            members_count=Count("memberships"),
            challenges_count=Count("challenges"),
        )
    )
    classrooms_joined = my_classrooms.count()

    # recently solved submissions
    recent_submissions = (
        Submission.objects.filter(user=request.user, status="passed")
        .select_related("challenge", "challenge__classroom")
        .order_by("-created_at")[:5]
    )

    # simple global rank (optional / rough)
    global_rank = None  # you can reuse your leaderboard logic later

    context = {
        "user": request.user,
        "total_solved": total_solved,
        "total_points": total_points,
        "classrooms_joined": classrooms_joined,
        "global_rank": global_rank,
        "my_classrooms": my_classrooms,
        "recent_submissions": recent_submissions,
    }
    return render(request, "dashboard.html", context)


# --------------- LEADERBOARD ENGINE ---------------
@login_required
def _compute_leaderboard(timeframe="all", classroom_id=None, limit=100):
    now = timezone.now()
    submissions = Submission.objects.filter(status="passed")

    # Time Filter
    if timeframe == "week":
        submissions = submissions.filter(created_at__gte=now - timedelta(days=7))
    elif timeframe == "month":
        submissions = submissions.filter(created_at__gte=now - timedelta(days=30))

    # Classroom Filter
    if classroom_id:
        submissions = submissions.filter(challenge__classroom_id=classroom_id)

    # Aggregation
    aggregated = (
        submissions.values("user", "user__username")
        .annotate(total=Sum("points_awarded"))
        .order_by("-total")[:limit]
    )

    # Fetch profiles
    user_ids = [row["user"] for row in aggregated]
    profiles = Profile.objects.filter(user_id__in=user_ids)
    profile_map = {p.user_id: p for p in profiles}

    # Final structured list
    leaderboard = []
    for index, row in enumerate(aggregated, start=1):
        leaderboard.append(
            {
                "rank": index,
                "user_id": row["user"],
                "username": row.get("user__username"),
                "total": row.get("total", 0),
                "profile": profile_map.get(row["user"]),
            }
        )

    return leaderboard

@login_required
def leaderboard_page(request):
    if not request.user.is_authenticated:
        return render(request, "not_found.html")

    timeframe = request.GET.get("time", "all")  # all, week, month
    classroom_param = request.GET.get("classroom")

    try:
        classroom_id = (
            int(classroom_param)
            if classroom_param is not None and classroom_param != "all"
            else None
        )
    except (TypeError, ValueError):
        classroom_id = None

    cache_key = f"leaderboard_{timeframe}_{classroom_id if classroom_id else 'all'}"
    leaderboard = cache.get(cache_key)

    if leaderboard is None:
        leaderboard = _compute_leaderboard(
            timeframe=timeframe, classroom_id=classroom_id, limit=200
        )
        cache.set(cache_key, leaderboard, timeout=300)

    user_rank = None
    for entry in leaderboard:
        if entry.get("user_id") == request.user.id:
            user_rank = entry.get("rank")
            break

    if not hasattr(request.user, "profile"):
        Profile.objects.create(user=request.user)
    user_points = request.user.profile.points

    selected_classroom = classroom_id
    selected_sort = request.GET.get("sort", "points")

    context = {
        "leaderboard": leaderboard,
        "user_rank": user_rank,
        "user_points": user_points,
        "selected_time": timeframe,
        "selected_classroom": selected_classroom,
        "selected_sort": selected_sort,
        "classrooms": Classroom.objects.all(),
    }

    return render(request, "leaderboard.html", context)

@login_required
def profile_page(request):
    if not request.user.is_authenticated:
        return render(request, "not_found.html")
    return render(request, "profile.html")


@staff_or_superuser_required
@login_required
def mentor_dashboard(request):
    mentor = request.user
    classrooms = Classroom.objects.filter(mentor=mentor)
    classrooms = classrooms.annotate(
        students_count=Count("memberships", distinct=True),
        challenges_count=Count("challenges", distinct=True),
        submissions_count=Count("challenges__submissions", distinct=True),
    )

    total_classrooms = classrooms.count()
    total_students = (
        classrooms.aggregate(total=Sum("students_count"))["total"] or 0
    )
    total_challenges = Challenge.objects.filter(
        classroom__in=classrooms
    ).count()
    total_submissions = Submission.objects.filter(
        challenge__classroom__in=classrooms
    ).count()


    recent_submissions = (
        Submission.objects.filter(challenge__classroom__in=classrooms)
        .select_related("user", "challenge")
        .order_by("-created_at")[:10]
    )

    context = {
        "classrooms": classrooms,
        "total_classrooms": total_classrooms,
        "total_students": total_students,
        "total_challenges": total_challenges,
        "total_submissions": total_submissions,
        "recent_submissions": recent_submissions,
    }

    return render(request, "mentor.html", context)
# --------------- CLASSROOMS ---------------

def classrooms_page(request):
    if not request.user.is_authenticated:
        return render(request, "not_found.html")

    # ---------- Stats used in student view ----------
    joined_classrooms_count = ClassroomMembership.objects.filter(
        user=request.user
    ).count()

    total_completed_challenges = Submission.objects.filter(
        user=request.user,
        status='passed'
    ).values("challenge").distinct().count()

    # ---------- Mentor view ----------
    if request.user.is_staff:
        # Only this mentor's classrooms
        classrooms = Classroom.objects.filter(
            mentor=request.user
        ).annotate(
            members_count=Count("memberships")
        )

        # Mentor stats
        mentor_active_classrooms = classrooms.count()

        mentor_total_students = ClassroomMembership.objects.filter(
            classroom__mentor=request.user
        ).values("user").distinct().count()

        mentor_total_challenges = Challenge.objects.filter(
            classroom__mentor=request.user
        ).count()

        # Avg completion: distinct (user, challenge) that passed
        total_passed = Submission.objects.filter(
            status='passed',
            challenge__classroom__mentor=request.user
        ).values("user", "challenge").distinct().count()

        total_possible = mentor_total_challenges * mentor_total_students
        mentor_avg_completion = 0
        if total_possible > 0:
            mentor_avg_completion = round((total_passed / total_possible) * 100)

        context = {
            "classrooms": classrooms,
            "mentor_active_classrooms": mentor_active_classrooms,
            "mentor_total_students": mentor_total_students,
            "mentor_total_challenges": mentor_total_challenges,
            "mentor_avg_completion": mentor_avg_completion,
            # student stats (not used in mentor branch, but safe to pass)
            "joined_classrooms_count": joined_classrooms_count,
            "total_completed_challenges": total_completed_challenges,
        }

    # ---------- Student view ----------
    else:
        classrooms = Classroom.objects.annotate(
            members_count=Count("memberships")
        )

        context = {
            "classrooms": classrooms,
            "joined_classrooms_count": joined_classrooms_count,
            "total_completed_challenges": total_completed_challenges,
        }

    return render(request, "classrooms.html", context)

def classroom_detail(request, slug=None):
    if not request.user.is_authenticated:
        return render(request, "not_found.html")

    classroom = get_object_or_404(
        Classroom.objects.annotate(members_count=Count("memberships")),
        slug=slug,
    )

    is_member = ClassroomMembership.objects.filter(
        user=request.user,
        classroom=classroom,
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
        return render(request, "not_found.html")

    classroom = get_object_or_404(Classroom, slug=slug)

    membership, created = ClassroomMembership.objects.get_or_create(
        user=request.user,
        classroom=classroom,
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
        classroom=classroom,
    )

    if membership.exists():
        membership.delete()
        messages.success(request, f"You left {classroom.name}.")
    else:
        messages.info(request, "You are not a member of this classroom.")

    return redirect("classrooms_page")



# ------------ CHALLENGES ------------

def challenge_list(request):
    challenges = Challenge.objects.all()
    tags = Tag.objects.all()
    classrooms = Classroom.objects.all()

    difficulty = request.GET.get("difficulty")
    classroom = request.GET.get("classroom")
    tag = request.GET.get("tag")
    search = request.GET.get("search", '')

    if search:
        challenges = challenges.filter(title__icontains=search)

    if difficulty and difficulty != "all":
        challenges = challenges.filter(difficulty=difficulty)

    if classroom:
        challenges = challenges.filter(classroom_id=classroom)

    if tag:
        challenges = challenges.filter(tags__id=tag)


    context = {
        "challenges": challenges,
        "classrooms": classrooms,
        "tags": tags,
        'search': search,
        "selected_difficulty": difficulty,
        "selected_classroom": classroom,
        "selected_tag": tag,
    }

    return render(request, "challenges.html", context)

class AddCommentView(View):
    def post(self, request, challenge_slug):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required'}, status=401)
            return redirect("login")

        challenge = get_object_or_404(Challenge, slug=challenge_slug)

        # تحقق مما إذا كان الطلب AJAX أم لا
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request - معالجة JSON
            try:
                data = json.loads(request.body)
                content = data.get('content', '').strip()
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        else:
            # Regular form submission
            content = request.POST.get("content", "").strip()

        if not content:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Comment cannot be empty'}, status=400)
            return redirect("challenge_detail", challenge_slug=challenge.slug)

        # إنشاء التعليق
        comment = Comment.objects.create(
            challenge=challenge,
            user=request.user,
            content=content,
        )

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # رد JSON للـ AJAX
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'user': request.user.username,
                    'content': comment.content,
                    'created_at': comment.created_at.isoformat(),
                }
            })
        
        # Regular request - إعادة توجيه
        return redirect("challenge_detail", challenge_slug=challenge.slug)

class ChallengeDetailView(View):
    def get(self, request, challenge_slug):
        if not request.user.is_authenticated:
            return render(request, "not_found.html")

        challenge = get_object_or_404(Challenge, slug=challenge_slug)

        # User submissions for this challenge
        submissions = challenge.submissions.filter(
            user=request.user
        ).order_by("-created_at")

        # All comments for this challenge (flat, no parent)
        comments_qs = challenge.comments.all().order_by("-created_at")

        # Pagination (5 comments per page)
        paginator = Paginator(comments_qs, 5)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "challenge": challenge,
            "submissions": submissions,
            "comments": page_obj,   # you can use this if needed
            "page_obj": page_obj,   # template already loops on page_obj
        }
        return render(request, "challenge_details.html", context)


@require_POST
@require_POST
def challenge_submit(request, challenge_slug):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Not authenticated"}, status=403)

        # 1) Get challenge
        challenge = get_object_or_404(Challenge, slug=challenge_slug)

        # 2) Read + validate code and language
        user_code = (request.POST.get("code") or "").strip()
        language = request.POST.get("language", "python")

        if not user_code:
            return JsonResponse({"error": "Code is required"}, status=400)

        valid_languages = {choice[0] for choice in Submission.LANGUAGE_CHOICES}
        if language not in valid_languages:
            language = "python"

        tests = challenge.hidden_tests or []

        # 3) Calculate attempt_number **for this user + this challenge only**
        previous_attempts = Submission.objects.filter(
            user=request.user,
            challenge=challenge,
        ).count()

        # 4) Create Submission (pending)
        submission = Submission.objects.create(
            user=request.user,
            challenge=challenge,
            code=user_code,
            language=language,
            status="pending",
            attempt_number=previous_attempts + 1,   # <--- this is the only place we set it
        )

        results = []
        all_passed = True

        # 5) Run tests
        for test in tests:
            test_input = test.get("input", "")
            expected_output = (test.get("output", "") or "").strip()

            ok, actual_output = run_python_code(user_code, test_input)
            actual_output = (actual_output or "").strip()

            passed = ok and (actual_output == expected_output)
            results.append(
                {
                    "input": test_input,
                    "expected": expected_output,
                    "user_output": actual_output,
                    "passed": passed,
                }
            )

            if not passed:
                all_passed = False

        # 6) Set status
        submission.status = "passed" if all_passed else "failed"
        submission.save(update_fields=["status"])

        # 7) Award points (your existing function)
        award_points_for_submission(submission)

        # 8) Return JSON including attempt_number
        return JsonResponse(
            {
                "status": submission.status,
                "results": results,
                "submission_id": submission.id,              # DB id
                "attempt_number": submission.attempt_number, # what we show
                "points_awarded": submission.points_awarded,
            }
        )

    except Exception as e:
        print("ERROR in challenge_submit:\n", traceback.format_exc())
        return JsonResponse(
            {"error": f"Server error: {type(e).__name__}: {e}"},
            status=500
        )


@require_POST
def run_tests_view(request, challenge_slug):
    challenge = get_object_or_404(Challenge, slug=challenge_slug)
    user_code = (request.POST.get("code") or "").strip()
    tests = challenge.hidden_tests or []

    results = []
    all_passed = True

    for test in tests:
        test_input = test.get("input", "")
        expected = (test.get("output", "") or "").strip()

        ok, output = run_python_code(user_code, test_input)
        output = (output or "").strip()

        passed = ok and (output == expected)
        if not passed:
            all_passed = False

        results.append(
            {
                "input": test_input,
                "expected": expected,
                "user_output": output,
                "passed": passed,
            }
        )

    status = "passed" if all_passed else "failed"

    return JsonResponse(
        {
            "status": status,
            "results": results,
        }
    )

def run_python_code(user_code: str, test_input: str):

    # Split the test input into lines (e.g. "7\n" -> ["7"])
    input_lines = test_input.splitlines()
    pointer = 0

    # Fake input()
    def fake_input(prompt=None):
        nonlocal pointer
        if pointer < len(input_lines):
            value = input_lines[pointer]
            pointer += 1
            return value
        # if code calls input() too many times, return empty string
        return ""

    # Fake print()
    output_lines = []

    def fake_print(*args, **kwargs):
        text = " ".join(str(a) for a in args)
        output_lines.append(text)

    # Environment in which user code runs
    env = {
        "input": fake_input,
        "print": fake_print,
        "range": range,
        "len": len,
        "int": int,
        "float": float,
        "str": str,
    }

    try:
        exec(user_code, env, {})
    except Exception as e:
        # we return a special marker so we see errors
        return False, f"__ERROR__ {type(e).__name__}: {e}"

    # Join all printed lines with newlines
    return True, "\n".join(output_lines) + "\n"

def award_points_for_submission(submission):

    # 1) Only passed submissions can get points
    if submission.status != "passed":
        # Ensure failed submissions give 0 points
        if submission.points_awarded != 0:
            submission.points_awarded = 0
            submission.save(update_fields=["points_awarded"])
        return

    # 2) Check if this user already got points for THIS challenge
    from .models import Submission, Profile  

    already_rewarded = Submission.objects.filter(
        user=submission.user,
        challenge=submission.challenge,
        status="passed",
        points_awarded__gt=0,
    ).exclude(id=submission.id).exists()

    if already_rewarded:
        if submission.points_awarded != 0:
            submission.points_awarded = 0
            submission.save(update_fields=["points_awarded"])
        return

    # 3) First time solving this challenge successfully → award points
    challenge_points = submission.challenge.points

    submission.points_awarded = challenge_points
    submission.save(update_fields=["points_awarded"])

    profile, _ = Profile.objects.get_or_create(user=submission.user)
    profile.points = (profile.points or 0) + challenge_points
    profile.save(update_fields=["points"])


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()