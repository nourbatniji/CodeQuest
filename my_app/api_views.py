from django.http import JsonResponse
from .models import Classroom,Challenge, Submission,Comment
import json
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

#api_view for classroom list
def classroom_list_api(request):
    """
    API to return all rows in JSON format
    GET /api/classrooms/
    """
    classrooms = Classroom.objects.all()
    data = []
    for c in classrooms:
        data.append({
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "description": c.description,
            "mentor": c.mentor.username,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return JsonResponse({"classrooms": data})

#api_view for dynamic challenge_detail page
def submit_challenge_api(request, slug):
    """
    POST /api/challenge/<slug>/submit/
    Body JSON: { "code": "...", "language": "python" }
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "POST method required."}, status=400)

    challenge = get_object_or_404(Challenge, slug=slug)

    try:
        data = json.loads(request.body)
        code = data.get("code", "")
        language = data.get("language", "python")
        status = data.get("status", "pending")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    if not code:
        return JsonResponse({"error": "Code is required."}, status=400)

    submission = Submission.objects.create(
        user=request.user,
        challenge=challenge,
        code=code,
        language=language,
        status=status 
    )
    def submission_to_dict(submission):
        return {
            "message": "Submission received.",
            "id": submission.id,
            "user": submission.user.id,
            "challenge": submission.challenge.id,
            "code": submission.code,
            "language": submission.language,
            "status": submission.status,
            "created_at": submission.created_at.isoformat(),
        }
    return JsonResponse({
        "submission":submission_to_dict(submission)
    })

#api_view for dynamic classroom_detail page
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

#api_view for adding comment dynamically in challenge_detail page
def add_comment_api(request, slug):
    """
    POST /api/challenge/<id>/comment/
    Body JSON: { "content": "..." }
    """
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

    # Convert the comment to a dictionary for return in JSON
    comment_dict = {
        "id": comment.id,
        "user": comment.user.username,
        "content": comment.content,
        "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }

    return JsonResponse({"message": "Comment added.", "comment": comment_dict})

