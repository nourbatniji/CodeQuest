from django.contrib import admin
from .models import (
    Classroom, ClassroomMembership, Challenge, Submission, Comment,
    Badge, UserBadge
)

# ---------- Classroom ----------
class ClassroomAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description']
    list_filter = ['mentor', 'created_at']
    list_display = ['name', 'mentor', 'created_at']
    fields = ['name', 'description', 'mentor', 'created_at']
    readonly_fields = ['created_at']

admin.site.register(Classroom, ClassroomAdmin)

# ---------- ClassroomMembership ----------
class ClassroomMembershipAdmin(admin.ModelAdmin):
    list_filter = ['user', 'classroom', 'joined_at']
    list_display = ['user', 'classroom', 'joined_at']
    fields = ['user', 'classroom', 'joined_at']
    readonly_fields = ['joined_at']

admin.site.register(ClassroomMembership, ClassroomMembershipAdmin)

# ---------- Challenge ----------
class ChallengeAdmin(admin.ModelAdmin):
    search_fields = ['title', 'description', 'tags']
    list_filter = ['difficulty', 'classroom', 'created_at']
    list_display = ['title', 'classroom', 'difficulty', 'created_at']
    fields = [
        'title', 'slug', 'classroom', 'description',
        'input_description', 'output_description',
        'sample_input', 'sample_output', 'example_explanation',
        'constraints', 'starter_code', 'hidden_tests',
        'difficulty', 'tags', 'created_at'
    ]
    readonly_fields = ['created_at']

admin.site.register(Challenge, ChallengeAdmin)

# ---------- Submission ----------
class SubmissionAdmin(admin.ModelAdmin):
    search_fields = ['code']
    list_filter = ['status', 'language', 'challenge', 'user', 'created_at']
    list_display = ['user', 'challenge', 'status', 'language', 'created_at']
    fields = ['user', 'challenge', 'code', 'status', 'language', 'created_at']
    readonly_fields = ['created_at']

admin.site.register(Submission, SubmissionAdmin)

# ---------- Comment ----------
class CommentAdmin(admin.ModelAdmin):
    search_fields = ['content']
    list_filter = ['user', 'challenge', 'created_at']
    list_display = ['user', 'challenge', 'content', 'created_at']
    fields = ['user', 'challenge', 'content', 'created_at']
    readonly_fields = ['created_at']

admin.site.register(Comment, CommentAdmin)

# ---------- Badge ----------
class BadgeAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description']
    list_filter = ['requirement_type']
    list_display = ['name', 'requirement_type']
    fields = ['name', 'description', 'requirement_type']

admin.site.register(Badge, BadgeAdmin)

# ---------- UserBadge ----------
class UserBadgeAdmin(admin.ModelAdmin):
    list_filter = ['user', 'badge', 'earned_date']
    list_display = ['user', 'badge', 'earned_date']
    fields = ['user', 'badge', 'earned_date']
    readonly_fields = ['earned_date']

admin.site.register(UserBadge, UserBadgeAdmin)