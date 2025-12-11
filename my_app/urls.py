from django.urls import path
from . import views, api_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login, name="login"),
    path("signup/", views.signup, name="signup"),
    path("signout/", views.signout, name="signout"),
    path("dashboard/", views.dashboard, name="dashboard"),

    # list page
    path("challenges/", views.challenge_list, name="challenge_list"),

    # DETAIL (slug-only, singular 'challenge')
    path("challenge/<slug:challenge_slug>/", views.ChallengeDetailView.as_view(),name="challenge_detail",),

    # comments
    path("challenge/<slug:challenge_slug>/comment/",views.AddCommentView.as_view(),name="add_comment",),

    # submit code
    path("challenge/<slug:challenge_slug>/submit/",views.challenge_submit,name="challenge_submit",),

    # run tests
    path("challenge/<slug:challenge_slug>/run-tests/",views.run_tests_view,name="run_tests",),

    path("leaderboard/", views.leaderboard_page, name="leaderboard"),
    path("leaderboard/classroom/<int:classroom_id>/",views.leaderboard_page,name="classroom_leaderboard",),

    path("profile/", views.profile_page, name="profile"),              
    path("mentor_dashboard/", views.mentor_dashboard, name="mentor_dashboard"),

    path("classrooms/", views.classrooms_page, name="classrooms_page"),
    path("mentor/classrooms/create/",views.mentor_create_classroom,name="mentor_create_classroom",),
    path("mentor/classrooms/<slug:classroom_slug>/challenges/create/", views.mentor_create_challenge,name="mentor_create_challenge",),
    path("classroom/<slug:slug>/", views.classroom_detail, name="classroom_detail"),
    path("classroom/<slug:slug>/join/", views.join_classroom, name="join_classroom"),
    path("classroom/<slug:slug>/leave/", views.leave_classroom, name="leave_classroom"),
    path("mentor/challenges/<slug:challenge_slug>/edit/",views.mentor_edit_challenge,name="mentor_edit_challenge",),


    path("profile/<str:username>/", views.profile_page, name="profile_detail"),  # any user



]