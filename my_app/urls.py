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

    #urls for api_views
    path('api/classrooms/', api_views.classroom_list_api, name='api_classroom_list'),
    path('api/classroom/<int:classroom_id>/', api_views.classroom_detail_api, name='api_classroom_detail'),
    path('api/challenge/<slug:slug>/submit/', api_views.submit_challenge_api, name='api_challenge_submit'),
    path('api/challenge/<slug:slug>/comment/',api_views.add_comment_api,name='api_comment_submit'),
    path('api/challenge/<slug:challenge_slug>/comments/', api_views.comments_list_api,name='api_comment_pagination'),
    path("api/global-stats/", api_views.global_stats_api, name="api_global_stats"),
    path("api/user-classrooms/", api_views.user_classrooms_api, name="user-classrooms-api"),
    path("api/mentor-classrooms/", api_views.mentor_classrooms_api, name="mentor_classrooms_api"),

    path('classrooms/', views.classrooms_page),
    path('classroom/<slug:slug>/', views.classroom_detail, name='classroom_detail'),
    path('classroom/<slug:slug>/join/', views.join_classroom, name='join_classroom'),
    path('classroom/<slug:slug>/leave/', views.leave_classroom, name='leave_classroom'),


]

