from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('login/', views.login),
    path('signup/', views.signup),
    path('dashboard/', views.dashboard),
    path('classrooms/', views.classrooms_page),
    path('classroom/<int:classroom_id>/', views.classroom_detail),
    path('challenges/', views.challenges_page),
    path('challenge/<int:challenge_id>/', views.challenge_detail),
    path('leaderboard/', views.leaderboard_page),
    path('profile/', views.profile_page),
    path('mentor-dashboard/', views.mentor_dashboard),
]

