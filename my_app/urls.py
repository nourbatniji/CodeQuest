from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('login', views.login),
    path('signup', views.signup),
    path('dashboard', views.dashboard),
    path('classrooms', views.classrooms_page),
    path('challenges', views.challenges_page),
    path('leaderboard', views.leaderboard_page),
    path('profile', views.profile_page),
]
