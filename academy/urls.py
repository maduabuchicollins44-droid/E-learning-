from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.course_list, name="course_list"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),
    path(
        "<int:course_id>/lesson/<int:lesson_id>/",
        views.lesson_detail,
        name="lesson_detail",
    ),
    path("accounts/register/", views.register, name="register"),
    # Custom authentication routes
    path("accounts/login/", views.custom_login, name="login"),
    path("accounts/logout/", views.custom_logout, name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("profile/", views.profile_view, name="profile"),
    
    # --- DEDICATED INSTRUCTOR PORTAL ROUTES ---
    path(
        "instructor/dashboard/",
        views.instructor_dashboard,
        name="instructor_dashboard",
    ),
    path(
        "instructor/course/<int:course_id>/manage/",
        views.instructor_course_manage,
        name="instructor_course_manage",
    ),

    # Quiz route matching lesson_id
    path(
        "lesson/<int:lesson_id>/quiz/",
        views.take_quiz,
        name="take_quiz",
    ),
    # Complaint & Support Routes
    path(
        "complaint/new/",
        views.submit_complaint,
        name="submit_complaint",
    ),
    path(
        "complaints/my/",
        views.my_complaints,
        name="my_complaints",
    ),
    # Community Forum Routes
    path("forum/", views.forum_list, name="forum_list"),
    path(
        "forum/<int:post_id>/",
        views.post_detail,
        name="post_detail",
    ),
    path(
        "course/<int:course_id>/certificate/",
        views.generate_certificate,
        name="generate_certificate",
    ),
    path("guest-login/", views.guest_login, name="guest_login"),
    path(
        "course/<int:course_id>/enroll/",
        views.enroll_course,
        name="enroll_course",
    ),
]
