from django.http import JsonResponse
from .models import Classroom, Challenge, Submission, Comment, Badge, UserBadge, check_user_badges,ClassroomMembership
import json
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Case, When, IntegerField, Value, F,Q
from django.db.models.functions import Coalesce
from .models_stats import UserStats, ClassroomStats, MentorDashboardStats, LeaderboardCache
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.decorators import login_required

@login_required
def mentor_classrooms_api(request):
    """
    API: Return classrooms created by the logged-in mentor
    GET /api/mentor-classrooms/
    """
    # الصفوف التي أنشأها المنتور
    classrooms = Classroom.objects.filter(mentor=request.user)

    data = []
    for c in classrooms:
        data.append({
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "description": c.description,
            "mentor": c.mentor.username,
            "members_count": c.member_count(),  # من الدالة الموجودة في الموديل
            "challenges_count": c.challenges.count(),  # عدد التحديات
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": c.updated_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(c, 'updated_at') else None,
        })

    return JsonResponse({"classrooms": data})

@login_required
def user_classrooms_api(request):
    """
    API: Return classrooms the logged-in user has joined
    GET /api/user-classrooms/
    """
    # Get all memberships of the current user
    memberships = ClassroomMembership.objects.filter(user=request.user)

    data = []
    for m in memberships:
        c = m.classroom
        data.append({
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "description": c.description,
            "mentor": c.mentor.username,
            "members_count": c.member_count(),  # from model method
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return JsonResponse({"classrooms": data})

#api_view for classroom list
# -----------------------
# Classroom List API
# -----------------------
def classroom_list_api(request):
    classrooms = Classroom.objects.all()
    data = [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "description": c.description,
            "mentor": c.mentor.username,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for c in classrooms
    ]
    return JsonResponse({"classrooms": data})


#api_view for dynamic challenge_detail page
# -----------------------
# Submit Challenge API
# -----------------------
def submit_challenge_api(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "POST method required."}, status=400)

    challenge = get_object_or_404(Challenge, slug=slug)

    try:
        data = json.loads(request.body)
        code = data.get("code", "").strip()
        language = data.get("language", "python")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    if not code:
        return JsonResponse({"error": "Code is required."}, status=400)

    # إنشاء submission
    submission = Submission.objects.create(
        user=request.user,
        challenge=challenge,
        code=code,
        language=language,
        status="pending",
        points_awarded=0
    )

    # تقييم الحل (منطق مؤقت للتحقق من الإجابة)
    is_correct = False
    if challenge.hidden_tests and "return" in code:
        is_correct = True

    # تحديد النقاط حسب الصعوبة
    difficulty_points = {"Easy": 10, "Medium": 20, "Hard": 30}
    points_awarded = difficulty_points.get(challenge.difficulty, 10) if is_correct else 0

    # تحديث حالة الـSubmission
    submission.status = "passed" if is_correct else "failed"
    submission.points_awarded = points_awarded
    submission.save()

    # تحديث نقاط المستخدم والمستوى والبادجات عند النجاح
    if is_correct:
        profile = getattr(request.user, "profile", None)
        if profile:
            profile.points += points_awarded

            # حساب المستوى
            if profile.points < 50:
                profile.level = "Beginner"
            elif profile.points < 150:
                profile.level = "Intermediate"
            else:
                profile.level = "Advanced"

            profile.save()

        check_user_badges(request.user)

    return JsonResponse({
        "submission": {
            "message": "Submission received.",
            "id": submission.id,
            "user": submission.user.id,
            "challenge": submission.challenge.id,
            "code": submission.code,
            "language": submission.language,
            "status": submission.status,
            "points_awarded": submission.points_awarded,
            "user_level": getattr(request.user.profile, "level", "Beginner") if is_correct else None,
            "created_at": submission.created_at.isoformat(),
        }
    })


# -----------------------
# Classroom Detail API
# -----------------------
def classroom_detail_api(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    members_count = classroom.memberships.count()
    challenges_count = classroom.challenges.count()
    comments_count = sum(c.comments.count() for c in classroom.challenges.all())

    data = {
        "id": classroom.id,
        "name": classroom.name,
        "description": classroom.description,
        "mentor": classroom.mentor.username,
        "stats": {
            "members_count": members_count,
            "challenges_count": challenges_count,
            "comments_count": comments_count
        }
    }
    return JsonResponse(data)


# -----------------------
# Add Comment API
# -----------------------
def add_comment_api(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "POST method required."}, status=400)

    challenge = get_object_or_404(Challenge, slug=slug)

    try:
        data = json.loads(request.body)
        content = data.get("content", "").strip()
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    if not content:
        return JsonResponse({"error": "Content is required."}, status=400)

    comment = Comment.objects.create(
        user=request.user,
        challenge=challenge,
        content=content,
        created_at=timezone.now()
    )

    comment_dict = {
        "id": comment.id,
        "user": comment.user.username,
        "content": comment.content,
        "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }

    return JsonResponse({"message": "Comment added.", "comment": comment_dict})


# -----------------------
# List Comments API
# -----------------------
def comments_list_api(request, challenge_slug):
    page = int(request.GET.get("page", 1))
    page_size = 5

    comments = Comment.objects.filter(challenge__slug=challenge_slug).order_by("-created_at")
    paginator = Paginator(comments, page_size)
    page_obj = paginator.get_page(page)

    data = {
        "comments": [
            {
                "id": c.id,
                "user": c.user.username,
                "content": c.content,
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for c in page_obj
        ],
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
        "page": page_obj.number,
        "total_pages": paginator.num_pages,
    }

    return JsonResponse(data)

# نقاط تقديرية حسب الصعوبة — اضبط القيم حسب سياساتك أو أضف حقل Challenge.points
DIFFICULTY_POINTS = {
    "easy": 10,
    "medium": 20,
    "hard": 40,
}

def _user_points_annotation():
    """
    عبارة عن تعابير Case/When لإجمالي النقاط من الـ Submission (status='passed').
    يعيد تعبير يمكن استخدامه في annotate.
    """
    return Sum(
        Case(
            When(submission__status="passed", submission__challenge__difficulty="easy", then=Value(DIFFICULTY_POINTS["easy"])),
            When(submission__status="passed", submission__challenge__difficulty="medium", then=Value(DIFFICULTY_POINTS["medium"])),
            When(submission__status="passed", submission__challenge__difficulty="hard", then=Value(DIFFICULTY_POINTS["hard"])),
            output_field=IntegerField(),
        )
    )




def global_stats_api(request):
    """
    Ultra-fast API for frontend polling.
    Returns:
      - leaderboard (cached from LeaderboardCache)
      - weekly_leaderboard (cached)
      - user_stats (from UserStats table)
      - classrooms (from ClassroomStats table, only user's classrooms)
      - mentor_stats (from MentorDashboardStats table)
    """

    user = request.user if request.user.is_authenticated else None

    # ------------------------------
    # 1) Leaderboard (from cache)
    # ------------------------------
    cache = LeaderboardCache.objects.first()  # نفترض وجود صف واحد فقط كـ singleton

    leaderboard = []
    weekly_leaderboard = []

    if cache:
        leaderboard = [
            {
                "username": u.get("username"),
                "points": u.get("points"),
                "solved": u.get("solved"),
            } for u in cache.top_users
        ]

        weekly_leaderboard = [
            {
                "username": u.get("username"),
                "points": u.get("points"),
                "solved": u.get("solved"),
            } for u in cache.weekly_top_users
        ]
        

    # ------------------------------
    # 2) User personal stats
    # ------------------------------
    user_stats = {}
    if user:
        try:
            stats = UserStats.objects.get(user=user)
            user_stats = {
                "challenges_solved": stats.challenges_solved,
                "total_points": stats.total_points,
                "classrooms_joined": stats.classrooms_joined,
                "global_rank": stats.global_rank,
                
                "in_progress": stats.challenges_in_progress,
                "not_started": stats.not_started_count,
                "submissions_count":stats.submissions_count,
                "comments_count":stats.comments_count,

                "average_solve_time" :stats.average_solve_time,
                "fastest_solve_time":stats.fastest_solve_time, 
                "last_submission_dat":stats.last_submission_date,
                "last_activity_date":stats.last_activity_date, 

                "points_this_week": stats.weekly_points,
                
            }
        except UserStats.DoesNotExist:
            pass

    # ------------------------------
    # 3) Classroom stats (only user's classrooms)
    # ------------------------------
    classroom_summaries = []

    if user:
        user_classrooms = Classroom.objects.filter(memberships__user=user)
        cstats = ClassroomStats.objects.filter(classroom__in=user_classrooms)

        for c in cstats:
            classroom_summaries.append({
                "classroom_id": c.classroom.id,
                "name": c.classroom.name,
                "slug": c.classroom.slug,
                "members_count": c.members_count,
                "challenges_count": c.solved_challenges_count,
                "comments_count": c.comments_count,
                "avg_completion_percent": c.average_completion,
                "avg_challenge_time": c.average_challenge_time,
            })

    # ------------------------------
    # 4) Mentor dashboard stats
    # ------------------------------
    mentor_stats = {}
    if user:
        try:
            mstats = MentorDashboardStats.objects.get(mentor=user)
            mentor_stats = {
                "my_classrooms_count": mstats.my_classrooms_count,
                "active_classrooms_count": mstats.active_classrooms_count,
                "total_students": mstats.total_students,
                "total_challenges": mstats.total_challenges,
                "total_submissions": mstats.total_submissions,
                "average_submission_per_student": mstats.average_submission_per_student,
            }
        except MentorDashboardStats.DoesNotExist:
            pass

    # ------------------------------
    # Final Output
    # ------------------------------
    payload = {
        "leaderboard": leaderboard,
        "weekly_leaderboard": weekly_leaderboard,
        "user_stats": user_stats,
        "classrooms": classroom_summaries,
        "mentor_stats": mentor_stats,
        "server_time": timezone.now().isoformat(),
    }

    return JsonResponse(payload, safe=False)