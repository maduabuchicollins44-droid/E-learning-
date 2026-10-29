from io import BytesIO
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from .forms import ProfileUpdateForm, UserUpdateForm
from .models import (
    Certificate,
    Choice,
    Comment,
    Complaint,
    Course,
    Enrollment,
    InstructorProfile,
    Lesson,
    Post,
    Question,
    Quiz,
    QuizSubmission,
    StudentProfile,
)


# Helper function to check if user is an instructor or staff member
def is_instructor(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
def course_list(request):
    query = request.GET.get('q', '').strip()
    courses = Course.objects.all()

    if query:
        courses = courses.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).distinct()

    return render(request, "academy/course_list.html", {
        "courses": courses,
        "query": query,
    })


def custom_login(request):
    # 1. Direct already logged in users based on explicit role
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("/admin/")
        elif request.user.is_staff:
            return redirect("instructor_dashboard")
        return redirect("course_list")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)

            # 2. Direct Super Admin directly to /admin/
            if user.is_superuser:
                return redirect("/admin/")

            # 3. Direct Lecturers/Staff to Instructor Portal
            if user.is_staff:
                return redirect("instructor_dashboard")

            # 4. Direct regular students directly to course catalog
            return redirect("course_list")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "registration/login.html", {"form": form})


# --- INSTRUCTOR PORTAL VIEWS ---
@login_required
@user_passes_test(is_instructor)
def instructor_dashboard(request):
    # If Superuser, show all courses; if Lecturer, show only courses assigned to them
    if request.user.is_superuser:
        courses = Course.objects.all()
    else:
        courses = Course.objects.filter(instructor=request.user)

    return render(
        request,
        "academy/instructor_dashboard.html",
        {"courses": courses},
    )


@login_required
@user_passes_test(is_instructor)
def instructor_course_manage(request, course_id):
    if request.user.is_superuser:
        course = get_object_or_404(Course, id=course_id)
    else:
        course = get_object_or_404(Course, id=course_id, instructor=request.user)

    lessons = course.lessons.all()
    enrollments = course.enrollments.all()

    return render(
        request,
        "academy/instructor_course_manage.html",
        {
            "course": course,
            "lessons": lessons,
            "enrollments": enrollments,
        },
    )


def guest_login(request):
    guest_user, created = User.objects.get_or_create(
        username='guest_user',
        defaults={'first_name': 'Guest', 'last_name': 'User'}
    )
    auth_login(request, guest_user)
    return redirect('course_list')


def custom_logout(request):
    logout(request)
    return redirect('login')


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            messages.success(
                request, f"Account created for {username}! You can now log in."
            )
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def lesson_detail(request, course_id, lesson_id):
    course = get_object_or_404(Course, pk=course_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
    return render(
        request,
        "academy/lesson_detail.html",
        {"course": course, "lesson": lesson},
    )


@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = Lesson.objects.filter(course=course)
    total_lessons = lessons.count()

    enrollment = Enrollment.objects.filter(
        user=request.user, course=course
    ).first()

    is_approved = enrollment and enrollment.status == 'APPROVED'
    is_pending = enrollment and enrollment.status == 'PENDING'

    certificate = Certificate.objects.filter(
        student=request.user, 
        course=course
    ).first()

    completed_lessons_count = 1 if certificate else 0
    
    if total_lessons > 0:
        progress_percentage = 100 if certificate else int((completed_lessons_count / total_lessons) * 100)
    else:
        progress_percentage = 0

    context = {
        'course': course,
        'lessons': lessons,
        'enrollment': enrollment,
        'is_approved': is_approved,
        'is_pending': is_pending,
        'total_lessons': total_lessons,
        'certificate': certificate,
        'progress_percentage': progress_percentage,
        'completed_lessons_count': completed_lessons_count,
    }
    return render(request, 'academy/course_detail.html', context)


@login_required
@require_POST
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    receipt_file = request.FILES.get('receipt')

    if not receipt_file:
        messages.error(
            request, 'Please select a payment receipt file before submitting.'
        )
        return redirect('course_detail', course_id=course.id)

    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user, course=course
    )
    enrollment.receipt = receipt_file
    enrollment.status = 'PENDING'
    enrollment.save()

    messages.success(
        request, 'Receipt uploaded successfully! Awaiting admin approval.'
    )
    return redirect('course_detail', course_id=course.id)


@login_required
def take_quiz(request, lesson_id):
    quiz = get_object_or_404(Quiz, lesson__id=lesson_id)
    questions = Question.objects.filter(quiz=quiz)

    if request.method == "POST":
        score = 0
        total_questions = questions.count()
        results = []

        for question in questions:
            selected_choice_id = request.POST.get(f"question_{question.id}")
            selected_choice = None
            is_correct = False

            if selected_choice_id:
                selected_choice = Choice.objects.get(pk=selected_choice_id)
                if selected_choice.is_correct:
                    score += 1
                    is_correct = True

            results.append({
                "question": question,
                "selected_choice": selected_choice,
                "is_correct": is_correct,
                "correct_choice": question.choices.filter(is_correct=True).first(),
            })

        percentage = (score / total_questions * 100) if total_questions > 0 else 0

        QuizSubmission.objects.update_or_create(
            student=request.user,
            quiz=quiz,
            defaults={
                "score": score,
                "total_questions": total_questions,
                "percentage": percentage,
            },
        )

        if percentage >= 50.0:
            Certificate.objects.get_or_create(
                student=request.user,
                course=quiz.lesson.course,
            )

        return render(
            request,
            "academy/quiz_result.html",
            {
                "quiz": quiz,
                "score": score,
                "total_questions": total_questions,
                "percentage": percentage,
                "results": results,
                "course": quiz.lesson.course,
                "passed": percentage >= 50.0,
            },
        )

    return render(
        request,
        "academy/take_quiz.html",
        {"quiz": quiz, "questions": questions},
    )


@login_required
def profile_view(request):
    profile, created = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        raw_matric = request.POST.get("matric_number", "").strip()

        request.user.first_name = request.POST.get("first_name", "")
        request.user.last_name = request.POST.get("last_name", "")
        request.user.email = request.POST.get("email", "")
        request.user.save()

        profile.matric_number = raw_matric if raw_matric else None
        profile.level = request.POST.get("level", "")
        profile.department = request.POST.get("department", "")
        profile.phone_number = request.POST.get("phone_number", "")
        profile.bio = request.POST.get("bio", "")

        if "profile_picture" in request.FILES:
            profile.profile_picture = request.FILES["profile_picture"]
        elif "profile_pic" in request.FILES:
            profile.profile_picture = request.FILES["profile_pic"]

        try:
            profile.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")
        except IntegrityError:
            messages.error(
                request,
                "This Matriculation Number is already assigned to another profile."
            )

    return render(request, "academy/profile.html", {
        "user": request.user,
        "profile": profile
    })


# --- COMPLAINTS & FEEDBACK VIEWS ---
@login_required
def submit_complaint(request):
    if request.method == "POST":
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        if subject and message:
            Complaint.objects.create(
                user=request.user, subject=subject, message=message
            )
            messages.success(request, "Your complaint has been submitted.")
            return redirect("my_complaints")
        else:
            messages.error(request, "Please fill in all fields.")

    return render(request, "academy/submit_complaint.html")


@login_required
def my_complaints(request):
    complaints = Complaint.objects.filter(user=request.user).order_by(
        "-created_at"
    )
    return render(
        request, "academy/my_complaints.html", {"complaints": complaints}
    )


# --- COMMUNITY FORUM VIEWS ---
@login_required
def forum_list(request):
    posts = Post.objects.all().order_by("-created_at")
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        if title and content:
            Post.objects.create(
                author=request.user, title=title, content=content
            )
            messages.success(request, "Discussion post published!")
            return redirect("forum_list")

    return render(request, "academy/forum_list.html", {"posts": posts})


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            Comment.objects.create(
                post=post, author=request.user, content=content
            )
            return redirect("post_detail", post_id=post.id)

    return render(request, "academy/post_detail.html", {"post": post})


# --- CERTIFICATE GENERATION ---
def generate_pdf_certificate(student_name, course_title, completion_date, cert_id):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Heading1'],
        fontSize=32,
        alignment=1,
        textColor=colors.HexColor('#007a43'),
    )
    subtitle_style = ParagraphStyle(
        'CertSub', parent=styles['Normal'], fontSize=16, alignment=1, spaceAfter=20
    )
    name_style = ParagraphStyle(
        'CertName',
        parent=styles['Heading2'],
        fontSize=26,
        alignment=1,
        textColor=colors.black,
    )
    body_style = ParagraphStyle(
        'CertBody', parent=styles['Normal'], fontSize=14, alignment=1
    )
    meta_style = ParagraphStyle(
        'CertMeta',
        parent=styles['Normal'],
        fontSize=11,
        alignment=1,
        textColor=colors.HexColor('#4b5563'),
    )

    story = [
        Spacer(1, 30),
        Paragraph('FEDERAL POLYTECHNIC IDAH', title_style),
        Spacer(1, 10),
        Paragraph('CERTIFICATE OF COMPLETION', subtitle_style),
        Spacer(1, 15),
        Paragraph('This is to certify that', body_style),
        Spacer(1, 15),
        Paragraph(f'<b>{student_name}</b>', name_style),
        Spacer(1, 15),
        Paragraph(
            'has successfully completed the course assessment for', body_style
        ),
        Spacer(1, 10),
        Paragraph(
            f'<b>{course_title}</b>',
            ParagraphStyle(
                'CourseTitle',
                parent=styles['Heading2'],
                fontSize=20,
                alignment=1,
                textColor=colors.HexColor('#007a43'),
            ),
        ),
        Spacer(1, 25),
        Paragraph(
            f'Date Issued: <b>{completion_date}</b> | Certificate ID: <b>#{cert_id}</b>',
            meta_style,
        ),
        Spacer(1, 20),
        Paragraph(
            '<i>Verified E-Learning Certification Portal</i>',
            ParagraphStyle(
                'CertFoot',
                parent=styles['Normal'],
                fontSize=10,
                alignment=1,
                textColor=colors.gray,
            ),
        ),
    ]

    doc.build(story)
    buffer.seek(0)
    return buffer


@login_required
def generate_certificate(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    
    cert, created = Certificate.objects.get_or_create(
        student=request.user, 
        course=course
    )

    student_name = request.user.get_full_name() or request.user.username
    completion_date = cert.issued_at.strftime("%B %d, %Y")
    cert_id = str(cert.id)

    pdf_buffer = generate_pdf_certificate(
        student_name=student_name,
        course_title=course.title,
        completion_date=completion_date,
        cert_id=cert_id
    )

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Certificate_{course.id}.pdf"'
    return response
