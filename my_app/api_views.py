from django.http import JsonResponse
from .models import Classroom, Challenge, Submission, Comment, Badge, UserBadge, check_user_badges
import json
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.paginator import Paginator

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
