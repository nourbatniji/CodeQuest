from django.urls import path
from . import views,api_views

urlpatterns = [
    path('', views.index),
    path('login/', views.login),
    path('signup/', views.signup),
    path('dashboard/', views.dashboard),
    path('classrooms/', views.classrooms_page),
    path('classroom/<int:classroom_id>/', views.classroom_detail),
    path('challenges/', views.challenges_page),
    path('challenge/<slug:slug>/', views.challenge_detail),
    path('leaderboard/', views.leaderboard_page),
    path('profile/', views.profile_page),
    path('mentor-dashboard/', views.mentor_dashboard),

    #urls for api_views
    path('api/classrooms/', api_views.classroom_list_api, name='api_classroom_list'),
    path('api/challenge/<slug:slug>/submit/', api_views.submit_challenge_api, name='api_challenge_submit'),
]

