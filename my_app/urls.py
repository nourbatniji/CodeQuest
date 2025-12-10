from django.urls import path
from . import views,api_views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.index),
    # Authentication
    path('login/', views.login),
    path('signup/', views.signup),
    path('signout/', views.signout),
 
    path('dashboard/', views.dashboard),

    path("challenges/", views.challenge_list, name="challenge_list"),
    path("challenge/<slug:slug>/", views.challenge_detail, name="challenge_detail"),
    
    path('leaderboard/', views.leaderboard_page),
    path('profile/', views.profile_page),
    path('mentor_dashboard/', views.mentor_dashboard),

    path('classrooms/', views.classrooms_page),
    path('classroom/<slug:slug>/', views.classroom_detail, name='classroom_detail'),
    path('classroom/<slug:slug>/join/', views.join_classroom, name='join_classroom'),
    path('classroom/<slug:slug>/leave/', views.leave_classroom, name='leave_classroom'),


]

