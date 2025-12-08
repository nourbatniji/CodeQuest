from django.db import models
from django.contrib.auth import get_user_model
from .models import Classroom, Challenge

User = get_user_model()


# ===============================
# User Statistics
# ===============================
class UserStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="stats")

    # General stats
    challenges_solved = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    classrooms_joined = models.IntegerField(default=0)
    global_rank = models.IntegerField(default=0)
    
    # Challenges progress
    challenges_not_started = models.IntegerField(default=0)#not need
    
    challenges_in_progress = models.IntegerField(default=0)
    not_started_count = models.IntegerField(default=0)
    submissions_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    
    # Time tracking
    average_solve_time = models.FloatField(default=0.0)  # بالثواني
    fastest_solve_time = models.FloatField(default=0.0)  # بالثواني
    last_submission_date = models.DateTimeField(null=True, blank=True)
    last_activity_date = models.DateTimeField(null=True, blank=True)

    # Points for this week
    weekly_points = models.IntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stats for {self.user.username}"


# ===============================
# Classroom Statistics
# ===============================
class ClassroomStats(models.Model):
    classroom = models.OneToOneField(Classroom, on_delete=models.CASCADE, related_name="stats")

    # Members & challenges
    members_count = models.IntegerField(default=0)
    total_challenges = models.IntegerField(default=0)
    solved_challenges_count = models.IntegerField(default=0)
    average_completion = models.FloatField(default=0.0)  # نسبة الحلول
    
    # Time tracking
    average_challenge_time = models.FloatField(default=0.0)  # بالثواني
    fastest_challenge_time = models.FloatField(default=0.0)
    
    # Activity
    comments_count = models.IntegerField(default=0)
    total_submissions = models.IntegerField(default=0)
    last_activity_date = models.DateTimeField(null=True, blank=True)

    # Optional: top performers for leaderboard
    top_performers = models.JSONField(default=list)  # [{"username": "Alex", "points": 2450}, ...]

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stats for {self.classroom.name}"


# ===============================
# Leaderboard Cache
# ===============================
class LeaderboardCache(models.Model):
    top_users = models.JSONField(default=list)  # [{"username": "Alex", "points": 2450, "solved": 87}, ...]
    weekly_top_users = models.JSONField(default=list)
    classroom_top_users = models.JSONField(default=dict)  # {classroom_id: [{"username": "Alex", "points": 100}, ...]}
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Leaderboard Cache"


# ===============================
# Mentor Dashboard Statistics
# ===============================
class MentorDashboardStats(models.Model):
    mentor = models.OneToOneField(User, on_delete=models.CASCADE, related_name="mentor_stats")
    
    # Overview
    my_classrooms_count = models.IntegerField(default=0)
    active_classrooms_count = models.IntegerField(default=0)
    total_students = models.IntegerField(default=0)
    total_challenges = models.IntegerField(default=0)
    total_submissions = models.IntegerField(default=0)
    
    # Optional analytics
    average_submission_per_student = models.FloatField(default=0.0)
    last_activity_date = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Mentor Dashboard Stats for {self.mentor.username}"
