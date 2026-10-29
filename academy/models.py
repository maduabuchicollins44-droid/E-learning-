import uuid

from django.contrib.auth.models import User
from django.db import models


# --- INSTRUCTOR / LECTURER PROFILE ---
class InstructorProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="instructor_profile"
    )
    department = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=50, default="Lecturer")  # e.g. Dr., Prof., Engr.
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="instructors/", default="default_avatar.png", blank=True
    )

    def __str__(self):
        return f"{self.title} {self.user.get_full_name() or self.user.username}"


class Course(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00)
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses_taught",
        limit_choices_to={"is_staff": True},
    )
    course_pdf = models.FileField(
        upload_to="course_pdfs/", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def user_passed_quiz(self, user):
        """Checks if user scored 50% or higher on any quiz in this course."""
        from .models import QuizSubmission
        return QuizSubmission.objects.filter(
            quiz__lesson__course=self,
            student=user,
            score__gte=50
        ).exists()


class Lesson(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lessons"
    )
    title = models.CharField(max_length=200)
    video_url = models.URLField(
        blank=True, help_text="Link to video (e.g., YouTube)"
    )
    content = models.TextField(help_text="Written lesson material")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Quiz(models.Model):
    lesson = models.OneToOneField(
        Lesson, on_delete=models.CASCADE, related_name="quiz"
    )
    title = models.CharField(max_length=200)

    def __str__(self):
        return f"Quiz for {self.lesson.title}"


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="questions"
    )
    text = models.TextField()

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class QuizSubmission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    percentage = models.FloatField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'total_questions') and self.total_questions and self.total_questions > 0:
            self.percentage = round(
                (self.score / self.total_questions) * 100, 2
            )
        else:
            self.percentage = 0.0

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} ({self.percentage}%)"


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()
    reference = models.CharField(max_length=100, unique=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = "PAY-" + str(uuid.uuid4().hex[:12]).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Paid" if self.verified else "Pending"
        return f"{self.user.username} - {self.course.title} ({status})"


class StudentProfile(models.Model):
    STATUS_CHOICES = (
        ("UNPAID", "Not Submitted"),
        ("PENDING", "Pending Approval"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    matric_number = models.CharField(
        max_length=50, blank=True, null=True, unique=True
    )
    department = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", default="default.jpg", blank=True
    )
    bio = models.TextField(blank=True, null=True)

    # Fee Verification Fields
    has_paid_fees = models.BooleanField(default=False)
    fee_receipt = models.FileField(upload_to="fee_receipts/", null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="UNPAID")
    rejection_reason = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.payment_status == "APPROVED":
            self.has_paid_fees = True
        else:
            self.has_paid_fees = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.payment_status}"


# --- COMPLAINTS / FEEDBACK MODEL ---
class Complaint(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="complaints"
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint by {self.user.username}: {self.subject}"


# --- COMMUNITY FORUM / DISCUSSION MODELS ---
class Post(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="forum_posts"
    )
    title = models.CharField(max_length=250)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.author.username}"


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"


class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"Certificate - {self.student.username} - {self.course.title}"


class Enrollment(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending Approval"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        "Course", on_delete=models.CASCADE, related_name="enrollments"
    )
    receipt = models.FileField(upload_to="receipts/", blank=True, null=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="PENDING"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.status})"
