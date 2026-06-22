from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import (
    Classroom, ClassroomMembership, Challenge, Submission, Comment,
    Badge, UserBadge, Tag, Profile
)

User = get_user_model()

class MentorRequestFilter(admin.SimpleListFilter):
    title = 'Mentor Requests'
    parameter_name = 'mentor_request'

    def lookups(self, request, model_admin):
        return [('pending', 'Pending Mentor Requests')]

    def queryset(self, request, queryset):
        if self.value() == 'pending':
            return queryset.filter(groups__name='Mentor Requests', is_staff=False)
        return queryset

class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_staff', 'is_pending_mentor']
    list_filter = UserAdmin.list_filter + (MentorRequestFilter,)
    actions = ['approve_as_mentor']

    def is_pending_mentor(self, obj):
        return obj.groups.filter(name='Mentor Requests').exists()
    is_pending_mentor.boolean = True
    is_pending_mentor.short_description = 'Pending Mentor'

    def approve_as_mentor(self, request, queryset):
        from django.contrib.auth.models import Group
        mentor_group = Group.objects.filter(name='Mentor Requests').first()
        for user in queryset:
            user.is_staff = True
            user.save()
            if mentor_group:
                user.groups.remove(mentor_group)
        self.message_user(request, f"{queryset.count()} user(s) approved as mentor.")
    approve_as_mentor.short_description = "Approve selected users as Mentor"

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

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
        'difficulty', 'tags','points', 'created_at'
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
admin.site.register(Tag)
admin.site.register(Profile)