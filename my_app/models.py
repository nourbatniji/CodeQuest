from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Classroom(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_classrooms")
    created_at = models.DateTimeField(auto_now_add=True)


class ClassroomMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

class Challenge(models.Model):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    DIFFICULTY_CHOICES = [
        (EASY, "Easy"),
        (MEDIUM, "Medium"),
        (HARD, "Hard"),
    ]

    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="challenges")
    description = models.TextField()
    input_description = models.TextField(blank=True)
    output_description = models.TextField(blank=True)
    sample_input = models.TextField(blank=True)
    sample_output = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default=EASY)
    tags = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Submission(models.Model):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (PASSED, "Passed"),
        (FAILED, "Failed"),
    ]

    PYTHON = "python"
    LANGUAGE_CHOICES = [
        (PYTHON, "Python"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="submissions")
    code = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default=PYTHON)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    points_awarded = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    created_at = models.DateTimeField(auto_now_add=True)


class Badge(models.Model):
    FIRST_SOLVE = "first_solve"
    CHALLENGE_COUNT = "challenge_count"
    CLASSROOM_COMPLETE = "classroom_complete"

    REQUIREMENT_CHOICES = [
        (FIRST_SOLVE, "First Solve"),
        (CHALLENGE_COUNT, "Challenge Count"),
        (CLASSROOM_COMPLETE, "Complete Classroom"),
    ]

    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    description = models.TextField()
    requirement_type = models.CharField(max_length=30, choices=REQUIREMENT_CHOICES)
    requirement_value = models.IntegerField(default=0)
    icon = models.CharField(max_length=100, blank=True)


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="awarded_users")
    awarded_at = models.DateTimeField(auto_now_add=True)


class Announcement(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="announcements")
    title = models.CharField(max_length=150)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="announcements_created")
    created_at = models.DateTimeField(auto_now_add=True)
    pinned = models.BooleanField(default=False)
