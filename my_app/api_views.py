from django.http import JsonResponse
from .models import Classroom,Challenge, Submission
import json
from django.shortcuts import get_object_or_404



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
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    if not code:
        return JsonResponse({"error": "Code is required."}, status=400)

    submission = Submission.objects.create(
        user=request.user,
        challenge=challenge,
        code=code,
        language=language,
        status=Submission.PENDING  
    )

    return JsonResponse({
        "message": "Submission received.",
        "submission_id": submission.id,
        "status": submission.status
    })

