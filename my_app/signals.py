from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Classroom, Submission, Comment, ClassroomMembership, Challenge, User
from .models_stats import UserStats, ClassroomStats, LeaderboardCache,MentorDashboardStats
import datetime

# -----------------------------
# 1) إنشاء UserStats عند إنشاء مستخدم
@receiver(post_save, sender=User)
def create_user_stats(sender, instance, created, **kwargs):
    if created:
        UserStats.objects.create(user=instance)
        
# إنشاء MentorDashboardStats عند إنشاء مستخدم mentor
@receiver(post_save, sender=User)
def create_mentor_stats(sender, instance, created, **kwargs):
    if created and instance.groups.filter(name="Mentor").exists():
        MentorDashboardStats.objects.create(mentor=instance)
# -----------------------------
# 2) إنشاء ClassroomStats عند إنشاء صف
@receiver(post_save, sender=Classroom) 
def create_classroom_stats(sender, instance, created, **kwargs):
    if created:
        ClassroomStats.objects.create(classroom=instance)

# -----------------------------
# 3) عند انضمام طالب إلى صف
@receiver(post_save, sender=ClassroomMembership)
def update_classroom_members(sender, instance, created, **kwargs):
    if created:
        stats = instance.classroom.stats
        stats.members_count += 1
        stats.last_activity_date = timezone.now()
        stats.save()
        # تحديث classrooms_joined للمستخدم
        user_stats = instance.user.stats
        user_stats.classrooms_joined += 1
        user_stats.last_activity_date = timezone.now()
        user_stats.save()

# -----------------------------
# 4) عند إضافة تحدي جديد
@receiver(post_save, sender=Challenge)
def update_classroom_challenges(sender, instance, created, **kwargs):
    if created:
        stats = instance.classroom.stats
        stats.total_challenges += 1
        stats.last_activity_date = timezone.now()
        stats.save()

# -----------------------------
# 5) عند إضافة تعليق
@receiver(post_save, sender=Comment)
def update_comment_stats(sender, instance, created, **kwargs):
    if created:
        # تحديث إحصائيات المستخدم
        user_stats = instance.user.stats
        user_stats.comments_count += 1
        user_stats.last_activity_date = timezone.now()
        user_stats.save()

        # تحديث إحصائيات الصف
        classroom_stats = instance.challenge.classroom.stats
        classroom_stats.comments_count += 1
        classroom_stats.last_activity_date = timezone.now()
        classroom_stats.save()

# -----------------------------
# 6) عند تقديم حل Submission
@receiver(post_save, sender=Submission)
def update_submission_stats(sender, instance, created, **kwargs):
    if not created:
        return

    user_stats, _ = UserStats.objects.get_or_create(user=instance.user)
    classroom_stats, _ = ClassroomStats.objects.get_or_create(classroom=instance.challenge.classroom)
    now = timezone.now()

    # تحديث عدد الحلول للمستخدم
    user_stats.submissions_count += 1
    user_stats.last_submission_date = now
    user_stats.last_activity_date = now

    # إذا كان الحل ناجح
    if instance.status == "passed":
        user_stats.challenges_solved += 1
        user_stats.total_points += instance.points_awarded
        # تحديث النقاط الأسبوعية
        week_start = now - datetime.timedelta(days=now.weekday())  # بداية الأسبوع
        user_stats.weekly_points += instance.points_awarded  # يمكن تعديل حسب logic الأسبوعي

        # تحديث وقت الحل
        if hasattr(instance, 'time_taken') and instance.time_taken:
            total_time = user_stats.average_solve_time * (user_stats.challenges_solved - 1)
            total_time += instance.time_taken
            user_stats.average_solve_time = total_time / user_stats.challenges_solved

            if user_stats.fastest_solve_time == 0 or instance.time_taken < user_stats.fastest_solve_time:
                user_stats.fastest_solve_time = instance.time_taken

        # تحديث إحصائيات الصف
        classroom_stats.solved_challenges_count += 1
        classroom_stats.total_submissions += 1
        # حساب average_completion
        if classroom_stats.total_challenges > 0:
            classroom_stats.average_completion = (
                classroom_stats.solved_challenges_count / classroom_stats.total_challenges
            )
        # تحديث متوسط وقت الحلول للصف
        if hasattr(instance, 'time_taken') and instance.time_taken:
            total_class_time = classroom_stats.average_challenge_time * (classroom_stats.solved_challenges_count - 1)
            total_class_time += instance.time_taken
            classroom_stats.average_challenge_time = total_class_time / classroom_stats.solved_challenges_count

            if classroom_stats.fastest_challenge_time == 0 or instance.time_taken < classroom_stats.fastest_challenge_time:
                classroom_stats.fastest_challenge_time = instance.time_taken

    classroom_stats.last_activity_date = now
    classroom_stats.save()
    user_stats.save()

# عند إنشاء صف جديد
@receiver(post_save, sender=Classroom)
def update_mentor_dashboard_classroom(sender, instance, created, **kwargs):
    if created:
        mentor = instance.mentor  # افترض أن الصف يحتوي على mentor
        mstats, _ = MentorDashboardStats.objects.get_or_create(mentor=mentor)
        mstats.my_classrooms_count += 1
        mstats.total_challenges += instance.challenges.count()  # لو الصف يحتوي على تحديات مسبقة
        mstats.total_students += instance.memberships.count()
        mstats.save()

# عند إضافة Submission
@receiver(post_save, sender=Submission)
def update_mentor_dashboard_submission(sender, instance, created, **kwargs):
    if created:
        mentor = instance.challenge.classroom.mentor
        mstats, _ = MentorDashboardStats.objects.get_or_create(mentor=mentor)
        mstats.total_submissions += 1
        mstats.save()

@receiver(post_save, sender=Submission)
def update_leaderboard_cache(sender, instance, created, **kwargs):
    if created and instance.status == "passed":
        # 1. تحديث جدول UserStats (هذا موجود بالفعل في signal سابق)
        # 2. تحديث Cache
        cache, _ = LeaderboardCache.objects.get_or_create(id=1)  # singleton
        top_users = UserStats.objects.order_by('-total_points', '-challenges_solved')[:10]
        cache.top_users = [
            {
                "username": u.user.username,
                "points": u.total_points,
                "solved": u.challenges_solved
            } for u in top_users
        ]
        # التحديث الأسبوعي
        week_start = timezone.now() - datetime.timedelta(days=timezone.now().weekday())
        weekly_top = UserStats.objects.filter(last_submission_date__gte=week_start).order_by('-weekly_points')[:10]
        cache.weekly_top_users = [
            {
                "username": u.user.username,
                "points": u.weekly_points,
                "solved": u.challenges_solved
            } for u in weekly_top
        ]
        cache.save()

    # ⚡ تحديث LeaderboardCache لاحقًا يمكن عمل task async مع Celery