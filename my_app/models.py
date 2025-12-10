from django.db import models
import re
from django.utils import timezone
from django.contrib.auth import get_user_model, authenticate
from django.utils.text import slugify
from django.core.validators import MinValueValidator    

User = get_user_model()

# ---------- AUTH HELPERS (not a manager) ----------

email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
pass_regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')


def is_exist(email):
    return User.objects.filter(email=email).exists()

def is_username_exist(username):
    return User.objects.filter(username=username).exists()

def validate_signup(postData):
    errors = {}

    if len(postData['username']) < 3 or len(postData['username']) > 25:
        errors['username_valid'] = 'Minimum 3 characters required'

    if not postData['username'].isalpha():
        errors['username_letter'] = 'Username must be letters only'

    if not email_regex.match(postData['email']):
        errors['email_valid'] = 'Invalid Email format'

    if is_username_exist(postData['username']):
        errors['not_unique_name'] = 'Username already exists'

    if is_exist(postData['email']):
        errors['not_unique'] = 'Email already exists'

    if not pass_regex.match(postData['password']) or len(postData['password']) > 128:
        errors['password_valid'] = 'Minimum 8 characters required, with upper, lower, digit, symbol'

    if postData['password'] != postData['confirm_pw']:
        errors['matching_pw'] = 'Passwords do not match!'

    return errors

def validate_login(postData):
    login_errors = {}

    if not email_regex.match(postData['email']):
        login_errors['login_email_valid'] = 'Invalid Email format'

    if not is_exist(postData['email']):
        login_errors['login_email_noexist'] = 'Email does not exist'

    if not pass_regex.match(postData['password']) or len(postData['password']) > 128:
        login_errors['login_pass_valid'] = 'Minimum 8 characters required'

    return login_errors

def create_user(postData):
    user = User.objects.create_user(
        username=postData['username'],
        email=postData['email'],
        password=postData['password']
    )
    user.is_staff = False
    user.is_superuser = False
    user.save()
    return user  

def authenticate_user(email, password): # gets the email to check the user pass
    try:
        user_obj = User.objects.get(email=email) #find user by email
    except User.DoesNotExist:
        return None
    
    user = authenticate(username=user_obj.username, password=password) #built-in django function=> reads hashed passwords from db, hash entered pass, compare them, if they match return user object,if not return None 
    #authenticate checks if password is correct
    return user

def get_user_by_email(email):
    return User.objects.filter(email=email)

def get_user_by_id(id):
    return User.objects.get(id=id)



# ---------- CLASSROOM MODELS ----------

class Classroom(models.Model):
    name = models.CharField(max_length=45)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(null=True, blank=True)
    mentor = models.ForeignKey(
        User,
        related_name='created_classrooms',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            n = 1
            while Classroom.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


    def member_count(self):
        return self.memberships.count()

    def __str__(self):  
        return self.name


class ClassroomMembership(models.Model):
    user = models.ForeignKey(
        User,
        related_name='user_joined_classes',
        on_delete=models.CASCADE
    )
    classroom = models.ForeignKey(
        Classroom,
        related_name='memberships',
        on_delete=models.CASCADE
    )
    joined_at = models.DateTimeField(auto_now_add=True)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    
class Challenge(models.Model):

    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="challenges")
    description = models.TextField()
    points = models.IntegerField(default=10,validators=[MinValueValidator(0)])
    input_description = models.TextField(blank=True)
    output_description = models.TextField(blank=True)
    sample_input = models.TextField(blank=True)
    sample_output = models.TextField(blank=True)
    example_explanation = models.TextField(blank=True)
    constraints = models.TextField(blank=True)
    starter_code = models.TextField(blank=True)
    hidden_tests = models.JSONField(default=dict) 
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            n = 1
            while Challenge.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)  

    def __str__(self):
        return self.title


class Submission(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("passed", "Passed"),
        ("failed", "Failed"),
    ]

    LANGUAGE_CHOICES = [
        ("python", "Python"),
        ("javascript", "JavaScript"),
        ("java", "Java"),
        ("cpp", "C++"),
        ("c", "C"),
        ("ruby", "Ruby"),
        ("go", "Go"),
        ("php", "PHP"),
        ("swift", "Swift"),
        ("kotlin", "Kotlin")
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="submissions")
    code = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='python')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    points_awarded = models.IntegerField(default=0,validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user}"


class Badge(models.Model):
    FIRST_SOLVE = "first_solve"
    CHALLENGE_COUNT = "challenge_count"
    CLASSROOM_COMPLETE = "classroom_complete"

    REQUIREMENT_CHOICES = [
        ("first_solve", "First Solve"),
        ("challenge_count", "Challenge Count"),
        ("classroom_complete", "Classroom Complete"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    requirement_type = models.CharField(max_length=30, choices=REQUIREMENT_CHOICES)
    value = models.IntegerField(default=0)
    icon = models.CharField(max_length=100, blank=True)

    users = models.ManyToManyField(
        User,
        through="UserBadge",
        related_name="badges"
    )

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "badge")

    def __str__(self):
        return f"{self.user} earned {self.badge}"


class Profile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('mentor', 'Mentor')
    ]

    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    level = models.CharField(max_length=20, default="Beginner")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    points = models.IntegerField(default=0,validators=[MinValueValidator(0)])
    def __str__(self):
        return f"{self.user.username} ({self.role})"
    
class ChallengeProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)

    status = models.CharField(max_length=20, choices=[
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'challenge')


def check_user_badges(user):
    solved_challenges = user.submissions.filter(status="passed").values_list("challenge", flat=True).distinct()
    solved_count = solved_challenges.count()
    badges = Badge.objects.all()

    for badge in badges:
        if UserBadge.objects.filter(user=user, badge=badge).exists():
            continue

        # FIRST SOLVE
        if badge.requirement_type == Badge.FIRST_SOLVE and solved_count >= 1:
            UserBadge.objects.create(user=user, badge=badge)
        # CHALLENGE COUNT
        if badge.requirement_type == Badge.CHALLENGE_COUNT and solved_count >= badge.value:
            UserBadge.objects.create(user=user, badge=badge)

        # CLASSROOM COMPLETE
        if badge.requirement_type == Badge.CLASSROOM_COMPLETE:
            # badge.value = classroom_id
            classroom_id = badge.value
            classroom = Classroom.objects.get(id=classroom_id)
            total_challenges = classroom.challenges.count()
            solved_in_class = classroom.challenges.filter(
                submissions__user=user,
                submissions__status="passed"
            ).distinct().count()

            if total_challenges > 0 and solved_in_class == total_challenges:
                UserBadge.objects.create(user=user, badge=badge)

def create_initial_badges():
    initial_badges = [
        {"name": "First Problem Solved", "desc": "Solve your first challenge!", "type": "first_solve", "value": 1},
        {"name": "5 Problems Solved", "desc": "Solved 5 challenges.", "type": "challenge_count", "value": 5},
        {"name": "10 Problems Solved", "desc": "Solved 10 challenges.", "type": "challenge_count", "value": 10},
        {"name": "20 Problems Solved", "desc": "Solved 20 challenges.", "type": "challenge_count", "value": 20},
        {"name": "30 Problems Solved", "desc": "Solved 30 challenges.", "type": "challenge_count", "value": 30},
        {"name": "40 Problems Solved", "desc": "Solved 40 challenges.", "type": "challenge_count", "value": 40},
        {"name": "50 Problems Solved", "desc": "Solved 50 challenges.", "type": "challenge_count", "value": 50},
    ]

    for b in initial_badges:
        Badge.objects.get_or_create(
            name=b["name"],
            requirement_type=b["type"],
            value=b["value"],
            defaults={"description": b["desc"]}
        )


