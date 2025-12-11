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
    check_user_badges,
    User
)
from django.contrib import messages
from django.db.models import Count, Q, Sum, F
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
from django.db.models.functions import Coalesce


from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Value, IntegerField
from django.shortcuts import render
from django.utils import timezone

from .models import Profile, Submission, Classroom, ClassroomMembership



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


@login_required
def profile_page(request, username=None):
    # 1) Which user's profile are we showing?
    if username is None:
        # /profile/  -> current logged-in user
        profile_user = request.user
    else:
        # /profile/<username>/ -> lookup by username
        profile_user = get_object_or_404(
            User.objects.select_related("profile"),
            username=username,
        )

    # 2) Total points = sum of points of all passed challenges
    total_points_data = (
        Submission.objects
        .filter(user=profile_user, status="passed")
        .aggregate(total=Sum("challenge__points"))
    )
    total_points = total_points_data["total"] or 0

    # 3) Challenges solved = number of DISTINCT challenges with at least one passed submission
    solved_count = (
        Submission.objects
        .filter(user=profile_user, status="passed")
        .values("challenge_id")
        .distinct()
        .count()
    )

    # 4) Recent submissions
    recent_submissions = (
        Submission.objects
        .filter(user=profile_user)
        .select_related("challenge")
        .order_by("-created_at")[:10]
    )

    # 5) Badges (if you have a ManyToMany on Profile)
    profile = profile_user.profile
    badges = profile.badges.all() if hasattr(profile, "badges") else []

    # 6) Skills (based on tags of passed submissions)
    skills = []
    tag_stats = (
        Submission.objects
        .filter(user=profile_user, status="passed", challenge__tags__isnull=False)
        .values("challenge__tags__id", "challenge__tags__name")
        .annotate(solved_count=Count("id"))
        .order_by("-solved_count")
    )

    max_count = tag_stats[0]["solved_count"] if tag_stats else 0
    for row in tag_stats[:6]:
        percentage = int(row["solved_count"] / max_count * 100) if max_count else 0
        skills.append({
            "name": row["challenge__tags__name"],
            "percentage": percentage,
            "solved_count": row["solved_count"],
        })

    context = {
        "profile_user": profile_user,
        "recent_submissions": recent_submissions,
        "badges": badges,
        "skills": skills,
        "total_points": total_points,
        "solved_count": solved_count,
    }
    return render(request, "profile.html", context)
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



# --------------- CHALLENGES ---------------
@login_required
@require_POST
def mentor_edit_challenge(request, challenge_slug):
    challenge = get_object_or_404(Challenge, slug=challenge_slug)
    classroom = challenge.classroom

    # permission: only classroom mentor, staff, or superuser
    if classroom.mentor != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You are not allowed to edit this challenge.")
        return redirect("classroom_detail", classroom.slug)

    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    points = request.POST.get("points", str(challenge.points)).strip()
    difficulty = request.POST.get("difficulty", challenge.difficulty)
    input_desc = request.POST.get("input_description", "").strip()
    output_desc = request.POST.get("output_description", "").strip()
    sample_input = request.POST.get("sample_input", "").strip()
    sample_output = request.POST.get("sample_output", "").strip()
    constraints = request.POST.get("constraints", "").strip()
    starter_code = request.POST.get("starter_code", "").strip()

    if not title or not description:
        messages.error(request, "Title and description are required.")
        return redirect("classroom_detail", classroom.slug)

    try:
        points = int(points)
    except ValueError:
        points = challenge.points

    challenge.title = title
    challenge.description = description
    challenge.points = points
    challenge.difficulty = difficulty
    challenge.input_description = input_desc
    challenge.output_description = output_desc
    challenge.sample_input = sample_input
    challenge.sample_output = sample_output
    challenge.constraints = constraints
    challenge.starter_code = starter_code
    challenge.save()

    messages.success(request, "Challenge updated successfully.")
    return redirect("classroom_detail", classroom.slug)



@require_POST
def mentor_create_challenge(request, classroom_slug):
    classroom = get_object_or_404(Classroom, slug=classroom_slug)

    # Only classroom mentor / staff can create
    if classroom.mentor != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You are not allowed to create challenges for this classroom.")
        return redirect("classroom_detail", classroom.id, classroom.slug)

    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    points = request.POST.get("points", "10").strip()
    difficulty = request.POST.get("difficulty", "easy")
    input_desc = request.POST.get("input_description", "").strip()
    output_desc = request.POST.get("output_description", "").strip()
    sample_input = request.POST.get("sample_input", "").strip()
    sample_output = request.POST.get("sample_output", "").strip()
    constraints = request.POST.get("constraints", "").strip()
    starter_code = request.POST.get("starter_code", "").strip()

    if not title or not description:
        messages.error(request, "Title and description are required.")
        return redirect("classroom_detail", classroom.id, classroom.slug)

    try:
        points = int(points)
    except ValueError:
        points = 10

    Challenge.objects.create(
        classroom=classroom,
        title=title,
        description=description,
        points=points,
        difficulty=difficulty,
        input_description=input_desc,
        output_description=output_desc,
        sample_input=sample_input,
        sample_output=sample_output,
        constraints=constraints,
        starter_code=starter_code,
        # hidden_tests uses default
    )

    messages.success(request, "Challenge created successfully.")
    return redirect("classroom_detail", classroom.slug)


# --------------- CLASSROOMS ---------------
@login_required
def mentor_create_classroom(request):
    # Only allow POST
    if request.method != "POST":
        return redirect("mentor_dashboard")  # change to your dashboard url name

    # Optional: check that user is mentor or staff
    is_mentor = request.user.groups.filter(name="Mentors").exists()
    if not (is_mentor or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to create a classroom.")
        return redirect("mentor_dashboard")

    # Get form data
    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()

    if not name:
        messages.error(request, "Classroom name is required.")
        return redirect("mentor_dashboard")

    # Create classroom; slug will be auto-generated by model.save()
    Classroom.objects.create(
        name=name,
        description=description,
        mentor=request.user,
    )

    messages.success(request, "Classroom created successfully.")
    return redirect("classrooms_page")

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

    # classroom with members + challenges counts
    classroom = get_object_or_404(
        Classroom.objects.annotate(
            members_count=Count("memberships", distinct=True),
            challenges_count=Count("challenges", distinct=True),
        ),
        slug=slug,
    )


    # is current user a member?
    is_member = ClassroomMembership.objects.filter(
        user=request.user,
        classroom=classroom,
    ).exists()
    
    # all challenges in this classroom
    challenges = classroom.challenges.all().prefetch_related("tags", "submissions")

    # build status per challenge
    challenge_entries = []
    completed_count = 0

    for ch in challenges:
        status = get_user_challenge_status(request.user, ch)
        challenge_entries.append({"challenge": ch, "status": status})
        if status == "passed":
            completed_count += 1

    total_challenges = challenges.count()

    # progress %
    progress_percent = 0
    if total_challenges:
        progress_percent = round((completed_count / total_challenges) * 100)

    context = {
        "classroom": classroom,
        "is_member": is_member,
        "members_count": classroom.members_count,
        "challenges_count": classroom.challenges_count,
        "challenges": challenges,              # raw list if you still need it
        "challenge_entries": challenge_entries,  # for status badges in template
        "completed_count": completed_count,
        "progress_percent": progress_percent,
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

def get_user_challenge_status(user, challenge):
    qs = challenge.submissions.filter(user=user)

    if not qs.exists():
        return "not_started"

    if qs.filter(status="passed").exists():
        return "passed"

    # has submissions but none passed
    return "failed"


def challenge_list(request):
    if not request.user.is_authenticated:
        return redirect("login")

    # --------------------------------------------------
    # 1) Decide base queryset depending on role
    # --------------------------------------------------

    # Classrooms where the user is the mentor
    mentor_classrooms = Classroom.objects.filter(mentor=request.user)

    if mentor_classrooms.exists():
        # USER IS A MENTOR → show challenges from their classrooms
        challenges = Challenge.objects.filter(
            classroom__in=mentor_classrooms
        )
        classrooms = mentor_classrooms
    else:
        # USER IS A STUDENT → show challenges from classrooms they joined
        joined_classroom_ids = ClassroomMembership.objects.filter(
            user=request.user
        ).values_list("classroom_id", flat=True)

        challenges = Challenge.objects.filter(
            classroom_id__in=joined_classroom_ids
        )
        classrooms = Classroom.objects.filter(
            id__in=joined_classroom_ids
        )

    # --------------------------------------------------
    # 2) Common filters (work for both mentor & student)
    # --------------------------------------------------
    tags = Tag.objects.all()

    difficulty = request.GET.get("difficulty")
    classroom = request.GET.get("classroom")
    tag = request.GET.get("tag")
    search = request.GET.get("search", "")

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
        "search": search,
        "selected_difficulty": difficulty,
        "selected_classroom": classroom,
        "selected_tag": tag,
    }

    return render(request, "challenges.html", context)


# my_app/views.py

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Value, IntegerField
from django.shortcuts import render
from django.utils import timezone

from .models import Profile, Submission, Classroom, ClassroomMembership


@login_required
def leaderboard_page(request):
    # ----------------- 1) Read filters from query string -----------------
    selected_time = request.GET.get("time", "all")          # all | week | month
    selected_classroom = request.GET.get("classroom", "all")  # all | classroom id
    selected_sort = request.GET.get("sort", "points")       # points | challenges | streak

    # ----------------- 2) Base queryset: all profiles --------------------
    profiles = Profile.objects.select_related("user")

    # ----------------- 3) Filter by classroom (if selected) -------------
    if selected_classroom != "all":
        try:
            classroom_id = int(selected_classroom)
            profiles = profiles.filter(
                user__classroommembership__classroom_id=classroom_id
            )
        except ValueError:
            # Invalid value – fall back to "all"
            selected_classroom = "all"

    classrooms = Classroom.objects.all()

    # ----------------- 4) Build submission queryset for solved ---------- 
    # We assume Submission has: user, status, created_at
    solved_submissions = Submission.objects.filter(status="passed")

    now = timezone.now()
    if selected_time == "week":
        solved_submissions = solved_submissions.filter(
            created_at__gte=now - timedelta(days=7)
        )
    elif selected_time == "month":
        solved_submissions = solved_submissions.filter(
            created_at__gte=now - timedelta(days=30)
        )
    # if "all", no date filter

    # ----------------- 5) Annotate stats on profiles --------------------
    # points  -> Profile.points (all-time)
    # solved_count -> how many passed submissions in selected time window
    # badges_count, streak -> dummy values (0) so template works
    profiles = profiles.annotate(
        solved_count=Count(
            "user__submissions",
            filter=Q(user__submissions__in=solved_submissions),
            distinct=True,
        ),
        badges_count=Value(0, output_field=IntegerField()),
        streak=Value(0, output_field=IntegerField()),
    )

    # ----------------- 6) Sorting --------------------------------------
    if selected_sort == "challenges":
        profiles = profiles.order_by("-solved_count", "-points", "user__username")
    elif selected_sort == "streak":
        profiles = profiles.order_by("-streak", "-points", "user__username")
    else:  # default: points
        profiles = profiles.order_by("-points", "-solved_count", "user__username")

    leaderboard = list(profiles)

    # ----------------- 7) Current user rank + points --------------------
    user_rank = None
    user_points = 0

    for idx, p in enumerate(leaderboard, start=1):
        if p.user_id == request.user.id:
            user_rank = idx
            user_points = p.points
            break

    week_start = now - timedelta(days=7)
    user_points_week = Submission.objects.filter(
        user=request.user,
        status="passed",
        created_at__gte=week_start,
    ).count()

    # ----------------- 9) Context for template -------------------------
    context = {
        "leaderboard": leaderboard,
        "classrooms": classrooms,
        "selected_time": selected_time,
        "selected_classroom": (
            int(selected_classroom) if selected_classroom not in ("", "all") else "all"
        ),
        "selected_sort": selected_sort,
        "user_rank": user_rank,
        "user_points": user_points,
        "user_points_week": user_points_week,
    }

    return render(request, "leaderboard.html", context)


class ChallengeDetailView(View):
    def get(self, request, challenge_slug):
        if not request.user.is_authenticated:
            return render(request, "not_found.html")

        challenge = get_object_or_404(Challenge, slug=challenge_slug)

        # User submissions for this challenge
        submissions = challenge.submissions.filter(
            user=request.user
        ).order_by("-created_at")

        # User-specific status for this challenge
        challenge_status = get_user_challenge_status(request.user, challenge)

        # All comments for this challenge
        comments_qs = challenge.comments.all().order_by("-created_at")

        paginator = Paginator(comments_qs, 5)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "challenge": challenge,
            "submissions": submissions,
            "comments": page_obj,
            "page_obj": page_obj,
            "challenge_status": challenge_status,
        }
        return render(request, "challenge_details.html", context)

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

        # User-specific status for this challenge
        challenge_status = get_user_challenge_status(request.user, challenge)

        # All comments for this challenge
        comments_qs = challenge.comments.all().order_by("-created_at")

        paginator = Paginator(comments_qs, 5)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "challenge": challenge,
            "submissions": submissions,
            "comments": page_obj,
            "page_obj": page_obj,
            "challenge_status": challenge_status,   # <<< NEW
        }
        return render(request, "challenge_details.html", context)


@require_POST
def challenge_submit(request, challenge_slug):
    # 1) Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=403)

    # 2) Get the challenge
    challenge = get_object_or_404(Challenge, slug=challenge_slug)

    # 3) Read and validate code
    user_code = (request.POST.get("code") or "").strip()
    language = request.POST.get("language", "python")

    if not user_code:
        return JsonResponse({"error": "Code is required"}, status=400)

    # 4) Validate language against Submission choices
    valid_languages = {choice[0] for choice in Submission.LANGUAGE_CHOICES}
    if language not in valid_languages:
        language = "python"

    # 5) Get hidden tests (list of dicts: {"input": "...", "output": "..."})
    tests = challenge.hidden_tests or []

    # 6) Count previous attempts for this user + challenge
    previous_attempts = Submission.objects.filter(
        user=request.user,
        challenge=challenge,
    ).count()
    attempt_number = previous_attempts + 1

    # 7) Create a new Submission with status "pending"
    submission = Submission.objects.create(
        user=request.user,
        challenge=challenge,
        code=user_code,
        language=language,
        status="pending",
        attempt_number=attempt_number,
    )

    all_passed = True
    results = []

    # 8) Run all hidden tests
    for test in tests:
        test_input = test.get("input", "")
        expected_output = (test.get("output", "") or "").strip()


        ok, actual_output = run_python_code(user_code, test_input)
        actual_output = (actual_output or "").strip()

        passed = ok and (actual_output == expected_output)

        results.append({
            "input": test_input,
            "expected": expected_output,
            "user_output": actual_output,
            "passed": passed,
        })

        if not passed:
            all_passed = False

    # 9) Update submission status
    submission.status = "passed" if all_passed else "failed"
    submission.save(update_fields=["status"])

    # 10) Award points (your helper can set submission.points_awarded internally)
    points_awarded = award_points_for_submission(submission)
    if submission.status == "passed":
        check_user_badges(request.user)

    # 11) Return response to the frontend
    return JsonResponse({
        "status": submission.status,
        "results": results,
        "submission_id": submission.id,
        "attempt_number": submission.attempt_number,
        "points_awarded": points_awarded,
    })


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