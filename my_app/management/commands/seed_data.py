from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from my_app.models import (
    Classroom, ClassroomMembership, Challenge, Tag,
    Submission, Badge, UserBadge, Profile, check_user_badges
)
import random

User = get_user_model()

# NOTE: All challenges use input()/print() style.
# Students read input with input() and print the answer with print().
# Hidden tests supply stdin lines and check stdout.

STARTER_TWO_SUM = '''\
nums = list(map(int, input().split()))
target = int(input())

# Your solution here
seen = {}
for i, n in enumerate(nums):
    if target - n in seen:
        print(seen[target - n], i)
        break
    seen[n] = i
'''

STARTER_PALINDROME = '''\
s = input()

# Your solution here
cleaned = ''.join(c.lower() for c in s if c.isalnum())
print(cleaned == cleaned[::-1])
'''

STARTER_FIZZBUZZ = '''\
n = int(input())

# Your solution here
for i in range(1, n + 1):
    if i % 15 == 0:
        print("FizzBuzz")
    elif i % 3 == 0:
        print("Fizz")
    elif i % 5 == 0:
        print("Buzz")
    else:
        print(i)
'''

STARTER_REVERSE_LIST = '''\
nums = list(map(int, input().split()))

# Your solution here
print(*reversed(nums))
'''

STARTER_CLIMBING = '''\
n = int(input())

# Your solution here
if n <= 2:
    print(n)
else:
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    print(b)
'''

STARTER_BINARY_SEARCH = '''\
nums = list(map(int, input().split()))
target = int(input())

# Your solution here
lo, hi = 0, len(nums) - 1
result = -1
while lo <= hi:
    mid = (lo + hi) // 2
    if nums[mid] == target:
        result = mid
        break
    elif nums[mid] < target:
        lo = mid + 1
    else:
        hi = mid - 1
print(result)
'''

STARTER_MERGE_SORT = '''\
nums = list(map(int, input().split()))

# Your solution here
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

print(*merge_sort(nums))
'''

STARTER_MAX_SUBARRAY = '''\
nums = list(map(int, input().split()))

# Your solution here
max_sum = cur = nums[0]
for n in nums[1:]:
    cur = max(n, cur + n)
    max_sum = max(max_sum, cur)
print(max_sum)
'''

STARTER_VALID_PARENS = '''\
s = input()

# Your solution here
stack = []
pairs = {')': '(', '}': '{', ']': '['}
for c in s:
    if c in '({[':
        stack.append(c)
    elif c in pairs:
        if not stack or stack[-1] != pairs[c]:
            print(False)
            exit()
        stack.pop()
print(not stack)
'''

STARTER_LONGEST_PALINDROME = '''\
s = input()

# Your solution here
res = ""
for i in range(len(s)):
    for start, end in [(i, i), (i, i+1)]:
        l, r = start, end
        while l >= 0 and r < len(s) and s[l] == s[r]:
            if r - l + 1 > len(res):
                res = s[l:r+1]
            l -= 1; r += 1
print(res)
'''

STARTER_WORD_SEARCH = '''\
m, n = map(int, input().split())
board = [input().split() for _ in range(m)]
word = input()

# Your solution here
def dfs(r, c, i):
    if i == len(word): return True
    if r < 0 or r >= m or c < 0 or c >= n or board[r][c] != word[i]: return False
    tmp, board[r][c] = board[r][c], "#"
    found = dfs(r+1,c,i+1) or dfs(r-1,c,i+1) or dfs(r,c+1,i+1) or dfs(r,c-1,i+1)
    board[r][c] = tmp
    return found

print(any(dfs(r, c, 0) for r in range(m) for c in range(n)))
'''

STARTER_DIGIT_SUM = '''\
n = input().strip()
print(sum(int(d) for d in n))
'''

STARTER_COUNT_VOWELS = '''\
s = input()
print(sum(1 for c in s if c.lower() in "aeiou"))
'''

STARTER_FIBONACCI = '''\
n = int(input())

a, b = 0, 1
for _ in range(n):
    a, b = b, a + b
print(a)
'''

STARTER_DUPLICATES = '''\
nums = list(map(int, input().split()))

seen = set()
dupes = []
for n in nums:
    if nums.count(n) > 1 and n not in seen:
        dupes.append(n)
        seen.add(n)
print(*sorted(dupes))
'''


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
                        'description': (
                            'Given a list of integers and a target, print the two indices that add up to the target.\n\n'
                            'Read the numbers from the first line (space-separated) and the target from the second line.'
                        ),
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'Line 1: space-separated integers\nLine 2: target integer',
                        'output_description': 'Two space-separated indices (0-based) that sum to target.',
                        'sample_input': '2 7 11 15\n9',
                        'sample_output': '0 1',
                        'constraints': '2 <= length <= 10^4\nExactly one valid answer exists.',
                        'starter_code': STARTER_TWO_SUM,
                        'tags': ['Arrays', 'Hash Table'],
                        'hidden_tests': [
                            {'input': '2 7 11 15\n9',  'output': '0 1'},
                            {'input': '3 2 4\n6',       'output': '1 2'},
                            {'input': '1 5 3 7\n8',     'output': '1 3'},
                        ],
                    },
                    {
                        'title': 'Valid Palindrome',
                        'description': (
                            'Read a string and print True if it is a palindrome (ignoring non-alphanumeric characters '
                            'and case), or False otherwise.'
                        ),
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'One line: the string to check.',
                        'output_description': 'True or False',
                        'sample_input': 'A man a plan a canal Panama',
                        'sample_output': 'True',
                        'constraints': '1 <= length <= 200000',
                        'starter_code': STARTER_PALINDROME,
                        'tags': ['String', 'Two Pointers'],
                        'hidden_tests': [
                            {'input': 'A man a plan a canal Panama', 'output': 'True'},
                            {'input': 'race a car',                   'output': 'False'},
                            {'input': 'Was it a car or a cat I saw', 'output': 'True'},
                        ],
                    },
                    {
                        'title': 'FizzBuzz',
                        'description': (
                            'Read an integer n. For each number from 1 to n, print "FizzBuzz" if divisible by both '
                            '3 and 5, "Fizz" if by 3, "Buzz" if by 5, or the number itself otherwise.'
                        ),
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'One integer n.',
                        'output_description': 'n lines, one answer per line.',
                        'sample_input': '5',
                        'sample_output': '1\n2\nFizz\n4\nBuzz',
                        'constraints': '1 <= n <= 10000',
                        'starter_code': STARTER_FIZZBUZZ,
                        'tags': ['Math', 'String'],
                        'hidden_tests': [
                            {'input': '5',  'output': '1\n2\nFizz\n4\nBuzz'},
                            {'input': '15', 'output': '1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz'},
                            {'input': '1',  'output': '1'},
                        ],
                    },
                    {
                        'title': 'Reverse a List',
                        'description': 'Read a list of integers (space-separated) and print them in reverse order.',
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'One line: space-separated integers.',
                        'output_description': 'The integers in reverse order, space-separated.',
                        'sample_input': '1 2 3 4 5',
                        'sample_output': '5 4 3 2 1',
                        'constraints': '1 <= length <= 5000',
                        'starter_code': STARTER_REVERSE_LIST,
                        'tags': ['Arrays'],
                        'hidden_tests': [
                            {'input': '1 2 3 4 5',    'output': '5 4 3 2 1'},
                            {'input': '10 20 30',     'output': '30 20 10'},
                            {'input': '42',           'output': '42'},
                        ],
                    },
                    {
                        'title': 'Climbing Stairs',
                        'description': (
                            'You can climb 1 or 2 steps at a time. Read n (number of stairs) and print '
                            'the number of distinct ways to reach the top.'
                        ),
                        'difficulty': 'easy', 'points': 15,
                        'input_description': 'One integer n.',
                        'output_description': 'Number of distinct ways.',
                        'sample_input': '3',
                        'sample_output': '3',
                        'constraints': '1 <= n <= 45',
                        'starter_code': STARTER_CLIMBING,
                        'tags': ['Dynamic Programming', 'Math'],
                        'hidden_tests': [
                            {'input': '1', 'output': '1'},
                            {'input': '2', 'output': '2'},
                            {'input': '3', 'output': '3'},
                            {'input': '5', 'output': '8'},
                        ],
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
                        'description': (
                            'Read a sorted list of integers and a target. Print the index of the target, '
                            'or -1 if not found.'
                        ),
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'Line 1: sorted space-separated integers\nLine 2: target',
                        'output_description': 'Index of target or -1.',
                        'sample_input': '-1 0 3 5 9 12\n9',
                        'sample_output': '4',
                        'constraints': '1 <= length <= 10000',
                        'starter_code': STARTER_BINARY_SEARCH,
                        'tags': ['Arrays', 'Binary Search'],
                        'hidden_tests': [
                            {'input': '-1 0 3 5 9 12\n9',  'output': '4'},
                            {'input': '-1 0 3 5 9 12\n2',  'output': '-1'},
                            {'input': '1 3 5 7 9\n1',      'output': '0'},
                            {'input': '1 3 5 7 9\n9',      'output': '4'},
                        ],
                    },
                    {
                        'title': 'Merge Sort',
                        'description': 'Read a list of integers and print them sorted in ascending order.',
                        'difficulty': 'medium', 'points': 20,
                        'input_description': 'One line: space-separated integers.',
                        'output_description': 'The sorted integers, space-separated.',
                        'sample_input': '38 27 43 3 9 82 10',
                        'sample_output': '3 9 10 27 38 43 82',
                        'constraints': '1 <= length <= 100000',
                        'starter_code': STARTER_MERGE_SORT,
                        'tags': ['Sorting', 'Recursion'],
                        'hidden_tests': [
                            {'input': '38 27 43 3 9 82 10', 'output': '3 9 10 27 38 43 82'},
                            {'input': '5 1 4 2 8',          'output': '1 2 4 5 8'},
                            {'input': '1',                  'output': '1'},
                            {'input': '3 1 2',              'output': '1 2 3'},
                        ],
                    },
                    {
                        'title': 'Maximum Subarray',
                        'description': 'Read a list of integers and print the maximum sum of any contiguous subarray.',
                        'difficulty': 'medium', 'points': 20,
                        'input_description': 'One line: space-separated integers.',
                        'output_description': 'The maximum subarray sum.',
                        'sample_input': '-2 1 -3 4 -1 2 1 -5 4',
                        'sample_output': '6',
                        'constraints': '1 <= length <= 100000',
                        'starter_code': STARTER_MAX_SUBARRAY,
                        'tags': ['Arrays', 'Dynamic Programming', 'Greedy'],
                        'hidden_tests': [
                            {'input': '-2 1 -3 4 -1 2 1 -5 4', 'output': '6'},
                            {'input': '1',                      'output': '1'},
                            {'input': '-1 -2 -3',               'output': '-1'},
                            {'input': '5 4 -1 7 8',            'output': '23'},
                        ],
                    },
                    {
                        'title': 'Valid Parentheses',
                        'description': (
                            'Read a string of bracket characters and print True if all brackets are '
                            'properly matched and closed, or False otherwise.'
                        ),
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'One line: a string of bracket characters.',
                        'output_description': 'True or False',
                        'sample_input': '()[]{} ',
                        'sample_output': 'True',
                        'constraints': '1 <= length <= 10000',
                        'starter_code': STARTER_VALID_PARENS,
                        'tags': ['String', 'Stack'],
                        'hidden_tests': [
                            {'input': '()[]{}', 'output': 'True'},
                            {'input': '(]',     'output': 'False'},
                            {'input': '{[()]}', 'output': 'True'},
                            {'input': '([)]',   'output': 'False'},
                        ],
                    },
                    {
                        'title': 'Longest Palindromic Substring',
                        'description': 'Read a string and print the longest palindromic substring.',
                        'difficulty': 'medium', 'points': 25,
                        'input_description': 'One line: the string.',
                        'output_description': 'The longest palindromic substring.',
                        'sample_input': 'babad',
                        'sample_output': 'bab',
                        'constraints': '1 <= length <= 1000',
                        'starter_code': STARTER_LONGEST_PALINDROME,
                        'tags': ['String', 'Dynamic Programming', 'Two Pointers'],
                        'hidden_tests': [
                            {'input': 'babad',  'output': 'bab'},
                            {'input': 'cbbd',   'output': 'bb'},
                            {'input': 'a',      'output': 'a'},
                            {'input': 'racecar','output': 'racecar'},
                        ],
                    },
                    {
                        'title': 'Word Search',
                        'description': (
                            'Read a grid of characters and a word. Print True if the word exists in the grid '
                            '(horizontally or vertically, no reuse of cells), or False otherwise.\n\n'
                            'First line: two integers m n (rows and columns).\n'
                            'Next m lines: n space-separated characters.\n'
                            'Last line: the word to find.'
                        ),
                        'difficulty': 'hard', 'points': 30,
                        'input_description': 'Line 1: m n\nLines 2..m+1: grid rows (space-separated chars)\nLast line: word',
                        'output_description': 'True or False',
                        'sample_input': '3 4\nA B C E\nS F C S\nA D E E\nABCCED',
                        'sample_output': 'True',
                        'constraints': '1 <= m, n <= 6\n1 <= word length <= 15',
                        'starter_code': STARTER_WORD_SEARCH,
                        'tags': ['Arrays', 'Recursion', 'Graphs'],
                        'hidden_tests': [
                            {'input': '3 4\nA B C E\nS F C S\nA D E E\nABCCED',  'output': 'True'},
                            {'input': '3 4\nA B C E\nS F C S\nA D E E\nSEE',     'output': 'True'},
                            {'input': '3 4\nA B C E\nS F C S\nA D E E\nABCB',    'output': 'False'},
                            {'input': '2 2\nA B\nC D\nABDC',                      'output': 'False'},
                        ],
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
                        'description': 'Read a non-negative integer and print the sum of its digits.',
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'One non-negative integer.',
                        'output_description': 'Sum of all digits.',
                        'sample_input': '1234',
                        'sample_output': '10',
                        'constraints': '0 <= n <= 10^9',
                        'starter_code': STARTER_DIGIT_SUM,
                        'tags': ['Math'],
                        'hidden_tests': [
                            {'input': '1234', 'output': '10'},
                            {'input': '0',    'output': '0'},
                            {'input': '999',  'output': '27'},
                            {'input': '100',  'output': '1'},
                        ],
                    },
                    {
                        'title': 'Count Vowels',
                        'description': 'Read a string and print the number of vowels (a, e, i, o, u — case insensitive).',
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'One line: the string.',
                        'output_description': 'Count of vowels.',
                        'sample_input': 'Hello World',
                        'sample_output': '3',
                        'constraints': '0 <= length <= 10000',
                        'starter_code': STARTER_COUNT_VOWELS,
                        'tags': ['String'],
                        'hidden_tests': [
                            {'input': 'Hello World',  'output': '3'},
                            {'input': 'aeiou',        'output': '5'},
                            {'input': 'xyz',          'output': '0'},
                            {'input': 'Python',       'output': '1'},
                        ],
                    },
                    {
                        'title': 'Fibonacci Sequence',
                        'description': 'Read n and print the nth Fibonacci number. F(0)=0, F(1)=1.',
                        'difficulty': 'easy', 'points': 10,
                        'input_description': 'One integer n.',
                        'output_description': 'The nth Fibonacci number.',
                        'sample_input': '6',
                        'sample_output': '8',
                        'constraints': '0 <= n <= 30',
                        'starter_code': STARTER_FIBONACCI,
                        'tags': ['Math', 'Recursion', 'Dynamic Programming'],
                        'hidden_tests': [
                            {'input': '0',  'output': '0'},
                            {'input': '1',  'output': '1'},
                            {'input': '6',  'output': '8'},
                            {'input': '10', 'output': '55'},
                        ],
                    },
                    {
                        'title': 'Find Duplicates',
                        'description': (
                            'Read a list of integers and print the duplicate values in sorted order '
                            '(values that appear more than once), space-separated.'
                        ),
                        'difficulty': 'medium', 'points': 20,
                        'input_description': 'One line: space-separated integers.',
                        'output_description': 'Sorted duplicates, space-separated.',
                        'sample_input': '4 3 2 7 8 2 3 1',
                        'sample_output': '2 3',
                        'constraints': '1 <= length <= 100000',
                        'starter_code': STARTER_DUPLICATES,
                        'tags': ['Arrays', 'Hash Table', 'Sorting'],
                        'hidden_tests': [
                            {'input': '4 3 2 7 8 2 3 1', 'output': '2 3'},
                            {'input': '1 1 2',            'output': '1'},
                            {'input': '1 2 3',            'output': ''},
                            {'input': '5 5 5 1 2',        'output': '5'},
                        ],
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
                challenge, created = Challenge.objects.update_or_create(
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

        self.stdout.write('  ✓ Classrooms and challenges created/updated')

        # ── Enroll students ───────────────────────────────────
        for student in students:
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
        self.stdout.write('\n  ⚠  All challenges use input()/print() style.')
        self.stdout.write('     Students read input with input() and print their answer with print().')
