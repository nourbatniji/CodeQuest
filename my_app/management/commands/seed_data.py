from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from my_app.models import (
    Classroom, ClassroomMembership, Challenge, Tag,
    Submission, Badge, UserBadge, Profile, check_user_badges
)
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with realistic sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # ── Tags ──────────────────────────────────────────────
        tag_names = [
            'Arrays', 'Hash Table', 'String', 'Two Pointers', 'Sorting',
            'Binary Search', 'Recursion', 'Dynamic Programming', 'Greedy',
            'Linked List', 'Stack', 'Queue', 'Trees', 'Graphs', 'Math',
        ]
        tags = {}
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            tags[name] = tag
        self.stdout.write('  ✓ Tags created')

        # ── Badges ────────────────────────────────────────────
        badge_data = [
            {'name': 'First Blood',      'description': 'Solved your first challenge!',    'requirement_type': 'first_solve',      'value': 1},
            {'name': 'Problem Solver',   'description': 'Solved 5 challenges.',            'requirement_type': 'challenge_count',  'value': 5},
            {'name': 'Code Master',      'description': 'Solved 10 challenges.',           'requirement_type': 'challenge_count',  'value': 10},
            {'name': 'Speed Demon',      'description': 'Solved 20 challenges.',           'requirement_type': 'challenge_count',  'value': 20},
            {'name': 'Algorithm Expert', 'description': 'Solved 30 challenges.',           'requirement_type': 'challenge_count',  'value': 30},
        ]
        for b in badge_data:
            Badge.objects.get_or_create(
                name=b['name'],
                requirement_type=b['requirement_type'],
                value=b['value'],
                defaults={'description': b['description']},
            )
        self.stdout.write('  ✓ Badges created')

        # ── Mentors ───────────────────────────────────────────
        mentor_data = [
            {'username': 'dr_sarah',   'email': 'sarah@codequest.com',   'first_name': 'Sarah',   'last_name': 'Johnson'},
            {'username': 'prof_james', 'email': 'james@codequest.com',   'first_name': 'James',   'last_name': 'Wilson'},
            {'username': 'dr_emma',    'email': 'emma@codequest.com',    'first_name': 'Emma',    'last_name': 'Rodriguez'},
        ]
        mentors = []
        for m in mentor_data:
            user, created = User.objects.get_or_create(
                username=m['username'],
                defaults={'email': m['email'], 'first_name': m['first_name'], 'last_name': m['last_name'], 'is_staff': True}
            )
            if created:
                user.set_password('Mentor@123')
                user.is_staff = True
                user.save()
                Profile.objects.get_or_create(user=user)
            mentors.append(user)
        self.stdout.write('  ✓ Mentors created')

        # ── Students ──────────────────────────────────────────
        student_data = [
            {'username': 'alex_chen',    'email': 'alex@example.com'},
            {'username': 'sofia_m',      'email': 'sofia@example.com'},
            {'username': 'liam_b',       'email': 'liam@example.com'},
            {'username': 'olivia_t',     'email': 'olivia@example.com'},
            {'username': 'noah_d',       'email': 'noah@example.com'},
            {'username': 'ava_j',        'email': 'ava@example.com'},
            {'username': 'james_w',      'email': 'jamesw@example.com'},
            {'username': 'isabella_g',   'email': 'isabella@example.com'},
        ]
        students = []
        for s in student_data:
            user, created = User.objects.get_or_create(
                username=s['username'],
                defaults={'email': s['email']}
            )
            if created:
                user.set_password('Student@123')
                user.save()
                Profile.objects.get_or_create(user=user)
            students.append(user)
        self.stdout.write('  ✓ Students created')

        # ── Classrooms & Challenges ───────────────────────────
        classroom_data = [
            {
                'name': 'Python Fundamentals',
                'description': 'Master the basics of Python programming with hands-on challenges.',
                'mentor': mentors[0],
                'challenges': [
                    {
                        'title': 'Two Sum',
                        'description': 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'An array of integers and a target integer.',
                        'output_description': 'Indices of the two numbers that add up to target.',
                        'sample_input': 'nums = [2,7,11,15]\ntarget = 9',
                        'sample_output': '[0, 1]',
                        'constraints': '2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\nExactly one valid answer exists.',
                        'starter_code': 'def two_sum(nums, target):\n    pass',
                        'tags': ['Arrays', 'Hash Table'],
                        'hidden_tests': [
                            {'input': '2 7 11 15\n9', 'output': '0 1'},
                            {'input': '3 2 4\n6', 'output': '1 2'},
                        ],
                    },
                    {
                        'title': 'Valid Palindrome',
                        'description': 'A phrase is a palindrome if, after converting all uppercase letters to lowercase and removing all non-alphanumeric characters, it reads the same forward and backward.',
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'A string s.',
                        'output_description': 'True if it is a palindrome, False otherwise.',
                        'sample_input': 's = "A man, a plan, a canal: Panama"',
                        'sample_output': 'True',
                        'constraints': '1 <= s.length <= 2 * 10^5\ns consists only of printable ASCII characters.',
                        'starter_code': 'def is_palindrome(s):\n    pass',
                        'tags': ['String', 'Two Pointers'],
                        'hidden_tests': [],
                    },
                    {
                        'title': 'FizzBuzz',
                        'description': 'Given an integer n, return a string array where each entry is "FizzBuzz" if divisible by 3 and 5, "Fizz" if by 3, "Buzz" if by 5, or the number as a string.',
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'An integer n.',
                        'output_description': 'A list of strings from 1 to n.',
                        'sample_input': '5',
                        'sample_output': '["1","2","Fizz","4","Buzz"]',
                        'constraints': '1 <= n <= 10^4',
                        'starter_code': 'def fizz_buzz(n):\n    pass',
                        'tags': ['Math', 'String'],
                        'hidden_tests': [],
                    },
                    {
                        'title': 'Reverse Linked List',
                        'description': 'Given the head of a singly linked list, reverse the list and return the reversed list.',
                        'difficulty': 'easy', 'points': 15,
                        'input_description': 'Head of a linked list.',
                        'output_description': 'Head of the reversed linked list.',
                        'sample_input': '[1,2,3,4,5]',
                        'sample_output': '[5,4,3,2,1]',
                        'constraints': '0 <= number of nodes <= 5000\n-5000 <= Node.val <= 5000',
                        'starter_code': 'def reverse_list(head):\n    pass',
                        'tags': ['Linked List', 'Recursion'],
                        'hidden_tests': [],
                    },
                    {
                        'title': 'Climbing Stairs',
                        'description': 'You are climbing a staircase. It takes n steps to reach the top. Each time you can climb 1 or 2 steps. In how many distinct ways can you climb to the top?',
                        'difficulty': 'easy', 'points': 15,
                        'input_description': 'An integer n.',
                        'output_description': 'Number of distinct ways to climb to the top.',
                        'sample_input': '3',
                        'sample_output': '3',
                        'constraints': '1 <= n <= 45',
                        'starter_code': 'def climb_stairs(n):\n    pass',
                        'tags': ['Dynamic Programming', 'Math'],
                        'hidden_tests': [],
                    },
                ],
            },
            {
                'name': 'Data Structures & Algorithms',
                'description': 'Deep dive into essential CS concepts and real-world problem-solving techniques.',
                'mentor': mentors[1],
                'challenges': [
                    {
                        'title': 'Binary Search',
                        'description': 'Given a sorted array of integers and a target, return the index of the target using binary search. Return -1 if not found.',
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'A sorted array and a target integer.',
                        'output_description': 'Index of the target, or -1.',
                        'sample_input': 'nums = [-1,0,3,5,9,12]\ntarget = 9',
                        'sample_output': '4',
                        'constraints': '1 <= nums.length <= 10^4\n-10^4 < nums[i], target < 10^4\nAll integers in nums are unique.',
                        'starter_code': 'def binary_search(nums, target):\n    pass',
                        'tags': ['Arrays', 'Binary Search'],
                        'hidden_tests': [],
                    },
                    {
                        'title': 'Merge Sort',
                        'description': 'Implement merge sort algorithm to sort an array in ascending order.',
                        'difficulty': 'medium', 'points': 20,
                        'input_description': 'An unsorted array of integers.',
                        'output_description': 'The sorted array.',
                        'sample_input': '[38, 27, 43, 3, 9, 82, 10]',
                        'sample_output': '[3, 9, 10, 27, 38, 43, 82]',
                        'constraints': '1 <= nums.length <= 10^5\n-10^5 <= nums[i] <= 10^5',
                        'starter_code': 'def merge_sort(nums):\n    pass',
                        'tags': ['Sorting', 'Recursion'],
                        'hidden_tests': [],
                    },
                    {
                        'title': 'Maximum Subarray',
                        'description': 'Given an integer array nums, find the subarray with the largest sum and return its sum.',
                        'difficulty': 'medium', 'points': 20,
                        'input_description': 'An array of integers nums.',
                        'output_description': 'The largest sum of any subarray.',
                        'sample_input': '[-2,1,-3,4,-1,2,1,-5,4]',
                        'sample_output': '6',
                        'constraints': '1 <= nums.length <= 10^5\n-10^4 <= nums[i] <= 10^4',
                        'starter_code': 'def max_subarray(nums):\n    pass',
                        'tags': ['Arrays', 'Dynamic Programming', 'Greedy'],
                        'hidden_tests': [],
                    },
                    {
                        'title': 'Valid Parentheses',
                        'description': 'Given a string s containing just the characters (, ), {, }, [ and ], determine if the input string is valid.',
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'A string of bracket characters.',
                        'output_description': 'True if the string is valid, False otherwise.',
                        'sample_input': '()[]{}"',
                        'sample_output': 'True',
                        'constraints': '1 <= s.length <= 10^4\ns consists of parentheses only.',
                        'starter_code': 'def is_valid(s):\n    pass',
                        'tags': ['String', 'Stack'],
                        'hidden_tests': [],
                    },
                    {
                        'title': 'Longest Palindromic Substring',
                        'description': 'Given a string s, return the longest palindromic substring in s.',
                        'difficulty': 'medium', 'points': 25,
                        'input_description': 'A string s.',
                        'output_description': 'The longest palindromic substring.',
                        'sample_input': 'babad',
                        'sample_output': 'bab',
                        'constraints': '1 <= s.length <= 1000\ns consists of only digits and English letters.',
                        'starter_code': 'def longest_palindrome(s):\n    pass',
                        'tags': ['String', 'Dynamic Programming', 'Two Pointers'],
                        'hidden_tests': [],
                    },
                    {
                        'title': 'Word Search',
                        'description': 'Given an m x n grid of characters board and a string word, return true if word exists in the grid.',
                        'difficulty': 'hard', 'points': 30,
                        'input_description': 'A 2D board and a target word.',
                        'output_description': 'True if the word exists in the grid.',
                        'sample_input': 'board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]]\nword = "ABCCED"',
                        'sample_output': 'True',
                        'constraints': 'm == board.length\nn = board[i].length\n1 <= m, n <= 6\n1 <= word.length <= 15',
                        'starter_code': 'def exist(board, word):\n    pass',
                        'tags': ['Arrays', 'Recursion', 'Graphs'],
                        'hidden_tests': [],
                    },
                ],
            },
            {
                'name': 'Web Development Bootcamp',
                'description': 'Build modern web applications and learn industry-standard development practices.',
                'mentor': mentors[2],
                'challenges': [
                    {
                        'title': 'Sum of Digits',
                        'description': 'Write a function that takes an integer and returns the sum of its digits.',
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'A non-negative integer n.',
                        'output_description': 'The sum of all digits in n.',
                        'sample_input': '1234',
                        'sample_output': '10',
                        'constraints': '0 <= n <= 10^9',
                        'starter_code': 'def digit_sum(n):\n    pass',
                        'tags': ['Math'],
                        'hidden_tests': [],
                    },
                    {
                        'title': 'Count Vowels',
                        'description': 'Write a function that counts the number of vowels (a, e, i, o, u) in a given string.',
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'A string s.',
                        'output_description': 'The count of vowels.',
                        'sample_input': 'Hello World',
                        'sample_output': '3',
                        'constraints': '0 <= s.length <= 10^4',
                        'starter_code': 'def count_vowels(s):\n    pass',
                        'tags': ['String'],
                        'hidden_tests': [],
                    },
                    {
                        'title': 'Fibonacci Sequence',
                        'description': 'Return the nth Fibonacci number. F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2).',
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'An integer n.',
                        'output_description': 'The nth Fibonacci number.',
                        'sample_input': '6',
                        'sample_output': '8',
                        'constraints': '0 <= n <= 30',
                        'starter_code': 'def fib(n):\n    pass',
                        'tags': ['Math', 'Recursion', 'Dynamic Programming'],
                        'hidden_tests': [],
                    },
                    {
                        'title': 'Find Duplicates',
                        'description': 'Given an array of integers, find all elements that appear more than once.',
                        'difficulty': 'medium', 'points': 20,
                        'input_description': 'An array of integers nums.',
                        'output_description': 'A list of all duplicate integers.',
                        'sample_input': '[4,3,2,7,8,2,3,1]',
                        'sample_output': '[2,3]',
                        'constraints': '1 <= nums.length <= 10^5\n1 <= nums[i] <= nums.length',
                        'starter_code': 'def find_duplicates(nums):\n    pass',
                        'tags': ['Arrays', 'Hash Table', 'Sorting'],
                        'hidden_tests': [],
                    },
                ],
            },
        ]

        classrooms = []
        all_challenges = []

        for cd in classroom_data:
            classroom, _ = Classroom.objects.get_or_create(
                name=cd['name'],
                defaults={'description': cd['description'], 'mentor': cd['mentor']}
            )
            classrooms.append(classroom)

            for chd in cd['challenges']:
                challenge, created = Challenge.objects.get_or_create(
                    title=chd['title'],
                    classroom=classroom,
                    defaults={
                        'description': chd['description'],
                        'difficulty': chd['difficulty'],
                        'points': chd['points'],
                        'input_description': chd.get('input_description', ''),
                        'output_description': chd.get('output_description', ''),
                        'sample_input': chd.get('sample_input', ''),
                        'sample_output': chd.get('sample_output', ''),
                        'constraints': chd.get('constraints', ''),
                        'starter_code': chd.get('starter_code', ''),
                        'hidden_tests': chd.get('hidden_tests', []),
                    }
                )
                if created:
                    for tag_name in chd.get('tags', []):
                        if tag_name in tags:
                            challenge.tags.add(tags[tag_name])
                all_challenges.append(challenge)

        self.stdout.write('  ✓ Classrooms and challenges created')

        # ── Enroll students ───────────────────────────────────
        for student in students:
            # each student joins 2–3 random classrooms
            for classroom in random.sample(classrooms, k=min(2, len(classrooms))):
                ClassroomMembership.objects.get_or_create(user=student, classroom=classroom)
        self.stdout.write('  ✓ Students enrolled in classrooms')

        # ── Sample submissions ────────────────────────────────
        statuses = ['passed', 'passed', 'passed', 'failed', 'failed']
        for student in students:
            joined = ClassroomMembership.objects.filter(user=student).values_list('classroom_id', flat=True)
            student_challenges = Challenge.objects.filter(classroom_id__in=joined)
            sample = random.sample(list(student_challenges), k=min(4, student_challenges.count()))
            profile, _ = Profile.objects.get_or_create(user=student)
            total_points = 0
            for ch in sample:
                status = random.choice(statuses)
                if not Submission.objects.filter(user=student, challenge=ch).exists():
                    Submission.objects.create(
                        user=student,
                        challenge=ch,
                        code=f'# Solution by {student.username}\nprint("hello")',
                        language='python',
                        status=status,
                        points_awarded=ch.points if status == 'passed' else 0,
                        attempt_number=1,
                    )
                    if status == 'passed':
                        total_points += ch.points
            profile.points = (profile.points or 0) + total_points
            profile.save()
            check_user_badges(student)

        self.stdout.write('  ✓ Sample submissions created')
        self.stdout.write(self.style.SUCCESS('\nDone! Sample data seeded successfully.'))
        self.stdout.write('  Mentor logins: dr_sarah / prof_james / dr_emma — password: Mentor@123')
        self.stdout.write('  Student logins: alex_chen / sofia_m / liam_b / ... — password: Student@123')
