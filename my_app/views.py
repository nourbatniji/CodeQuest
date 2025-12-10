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


def index(request):
    return render(request, "index.html")


# =======================
#        SIGNUP
# =======================
def signup(request):
    if request.method == "POST":
        errors = models.validate_signup(request.POST)
        if errors:
            return render(request, "signup.html", {"errors": errors})

        user = models.create_user(request.POST)
        Profile.objects.create(user=user)
        auth_login(request, user)

        return redirect("/dashboard")

    return render(request, "signup.html")


# =======================
#        LOGIN
# =======================
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


def dashboard(request):
    if not request.user.is_authenticated:
        return render(request, "not_found.html")
    context = {
        "user": request.user,
        "user_classes_count": request.user.user_joined_classes.count(),
    }
    return render(request, "dashboard.html", context)


# =====================================================
#                NEW LEADERBOARD ENGINE
# =====================================================
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


def profile_page(request):
    if not request.user.is_authenticated:
        return render(request, "not_found.html")
    return render(request, "profile.html")


@staff_or_superuser_required
def mentor_dashboard(request):
    if not request.user.is_authenticated:
        return render(request, "not_found.html")
    return render(request, "mentor.html")


# =======================
#       CLASSROOMS
# =======================
def classrooms_page(request):
    if not request.user.is_authenticated:
        return render(request, "not_found.html")

    classrooms = Classroom.objects.annotate(members_count=Count("memberships"))
    return render(request, "classrooms.html", {"classrooms": classrooms})


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
    classroom_id = request.GET.get("classroom")
    tag_id = request.GET.get("tag")

    try:
        classroom_id = int(classroom_id)
    except (TypeError, ValueError):
        classroom_id = None

    try:
        tag_id = int(tag_id)
    except (TypeError, ValueError):
        tag_id = None

    if difficulty and difficulty != "all":
        challenges = challenges.filter(difficulty__iexact=difficulty)

    if classroom_id:
        challenges = challenges.filter(classroom_id=classroom_id)

    if tag_id:
        challenges = challenges.filter(tags__id=tag_id)

    context = {
        "challenges": challenges,
        "classrooms": classrooms,
        "tags": tags,
        "selected_difficulty": difficulty,
        "selected_classroom": classroom_id,
        "selected_tag": tag_id,
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
def challenge_submit(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=403)

    # Get the challenge from the database (or 404 if slug is wrong)
    challenge = get_object_or_404(Challenge, slug=slug)

    # 3) Read the user's code from the form (textarea named "code")
    user_code = request.POST.get("code", "")

    # 4) Get this challenge's hidden tests (list of {input, output} objects)
    tests = challenge.hidden_tests or []  # if None → use []

    # 5) Create a Submission row in the database with status "pending"
    submission = Submission.objects.create(
        user=request.user,
        challenge=challenge,
        code=user_code,
        language="python",
        status="pending",
    )

    results = []  # will hold details for each test
    all_passed = True  # assume everything will pass at the start

    # 6) Run the user's code on each test case
    for test in tests:
        test_input = test.get("input", "")
        expected_output = (test.get("output", "") or "").strip()

        # run_python_code returns (ok, output)
        ok, actual_output = run_python_code(user_code, test_input)
        actual_output = (actual_output or "").strip()

        # Test passes only if:
        # - code ran without internal error (ok == True)
        # - and the printed output matches the expected output
        passed = ok and (actual_output == expected_output)

        # Save this test's result (for the frontend UI)
        results.append(
            {
                "input": test_input,
                "expected": expected_output,
                "user_output": actual_output,
                "passed": passed,
            }
        )

        # If any test fails → overall result is failed
        if not passed:
            all_passed = False

    # 7) Update the Submission status and points
    if all_passed:
        submission.status = "passed"
        submission.points_awarded = challenge.points
    else:
        submission.status = "failed"
        submission.points_awarded = 0

    submission.save()  # write changes to the database

    # 8) Send a JSON response back to the frontend
    return JsonResponse(
        {
            "status": submission.status,
            "results": results,
            "submission_id": submission.id,
        }
    )


@require_POST
def run_tests_view(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug)
    user_code = request.POST.get("code", "")
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
                "output": output,
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
    """
    Very simple runner:
    - replaces input() with our own function that reads from test_input
    - replaces print() so we can capture the output
    """

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
