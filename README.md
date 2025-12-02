# CodeQuest – Classroom Coding Challenge Platform  

A Django-based web application where developers (students) join classrooms, solve curated coding challenges, discuss problems, and earn achievements. Mentor developers create and manage all challenges through Django Admin.

This project follows the 10-day AXSOS Project Week workflow, using Scrum methodology, responsive design, AJAX, and AWS deployment.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Pages](#system-pages)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Models](#database-models)
- [API Endpoints](#api-endpoints)
- [Installation & Setup](#installation--setup)
- [Running the Project](#running-the-project)
- [Deployment](#deployment)
- [Team & Workflow](#team--workflow)
- [License](#license)

---

## Overview

CodeQuest is a classroom-based coding challenge platform where:

### Mentors (Admin Developers) can:
- Create classrooms  
- Add coding challenges  
- Post announcements  
- Monitor student progress  

### Students can:
- Join any classroom  
- Solve coding challenges  
- Track progress  
- Participate in discussion threads  
- Earn badges based on milestones  

This simulates a guided coding-learning environment inspired by platforms like HackerRank, LeetCode, and online classrooms.

---

## Features

### Authentication
- Login and registration with validation  
- Django's built-in authentication system  
- Admin accounts created via Django Admin  

### Classrooms
- Public list of all classrooms  
- Join a classroom  
- View classroom details (challenges, members, leaderboard)

### Challenges
- Mentor-created challenges only  
- Problem details include description, input/output format, and samples  
- Students solve challenges through a built-in code editor  

### Submissions
- Submit solutions  
- Track progress per challenge  
- Multiple submissions per challenge stored  

### Discussions (AJAX)
- Add comments under each challenge  
- Threaded replies  
- Comments update dynamically using AJAX  

### Achievements / Badges
- Earn badges for completing certain milestones  
- Examples: first solve, five solves, ten solves, classroom completion  

### Announcements
- Mentors post updates for classroom members  

### Responsive UI
- All pages responsive for mobile, tablet, and desktop  

---

## System Pages

Required pages:

1. Login page  
2. Registration page  
3. About Us page  
4. Dashboard (student or mentor)  
5. Functional pages (classrooms, challenges, profiles)

Additional functional pages:

- Classrooms list  
- Classroom detail  
- Challenge solve page  
- Profile/badge page  
- Announcements page  

---

## Tech Stack

### Backend
- Django  
- Django ORM  
- SQLite or MySQL  

### Frontend
- HTML  
- CSS (Bootstrap or Tailwind)  
- JavaScript  
- AJAX (Fetch API)

### Deployment
- AWS EC2 or Lightsail  
- Nginx  
- Gunicorn  

### Development Tools
- Git & GitHub  
- Trello  
- Balsamiq (wireframes)  
- MySQL Workbench (ERD)  
- VS Code  

---

## Project Structure

```text
codequest/
│
├── accounts/          # Authentication, profiles
├── classrooms/        # Classroom pages, membership, leaderboard
├── challenges/        # Challenges, submissions, comments
│
├── templates/         # HTML templates
├── static/            # CSS, JS, images
│
├── manage.py
├── requirements.txt
└── README.md
