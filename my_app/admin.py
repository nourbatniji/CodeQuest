from django.contrib import admin
from .models import (
    Classroom, ClassroomMembership, Challenge, Submission, Comment,
    Badge, UserBadge
)

def create_admin(model, search_fields=None, list_filter=None):
    class CustomAdmin(admin.ModelAdmin):
        list_display = [field.name for field in model._meta.fields]

    if search_fields:
        setattr(CustomAdmin, 'search_fields', search_fields)
    if list_filter:
        setattr(CustomAdmin, 'list_filter', list_filter)

    return CustomAdmin

admin.site.register(
    Classroom,
    create_admin(Classroom, search_fields=['name', 'description'], list_filter=['mentor', 'created_at'])
)

admin.site.register(
    ClassroomMembership,
    create_admin(ClassroomMembership, list_filter=['user', 'classroom', 'joined_at'])
)

admin.site.register(
    Challenge,
    create_admin(
        Challenge,
        search_fields=['title', 'description', 'tags'],
        list_filter=['difficulty', 'classroom', 'created_at']
    )
)

admin.site.register(
    Submission,
    create_admin(
        Submission,
        search_fields=['code'],
        list_filter=['status', 'language', 'challenge', 'user', 'created_at']
    )
)

admin.site.register(
    Comment,
    create_admin(
        Comment,
        search_fields=['content'],
        list_filter=['user', 'challenge', 'created_at']
    )
)

admin.site.register(
    Badge,
    create_admin(
        Badge,
        search_fields=['name', 'description'],
        list_filter=['requirement_type']
    )
)

admin.site.register(
    UserBadge,
    create_admin(
        UserBadge,
        list_filter=['user', 'badge', 'earned_date']
    )
)
