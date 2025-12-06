from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('login/', views.login),
    path('signup/', views.signup),
    path('signout/', views.signout),
    path('dashboard/', views.dashboard),
    path('classrooms/', views.classrooms_page),
    path('classroom/<int:classroom_id>/', views.classroom_detail),
    path('challenges/', views.challenges_page),
    path('challenge/<int:challenge_id>/', views.challenge_detail),
    path('leaderboard/', views.leaderboard_page),
    path('profile/', views.profile_page),
    path('mentor-dashboard/', views.mentor_dashboard),
    path('<slug:slug>/join/', views.join_classroom, name='join_classroom'),
    path('<slug:slug>/leave/', views.leave_classroom, name='leave_classroom'),
    path('<slug:classroom_slug>/create/', views.create_challenge, name="create_challenge"),
    path('list/', views.challenge_list, name="challenge_list"),
]

