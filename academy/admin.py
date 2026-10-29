from django.contrib import admin
from .models import (
    Choice,
    Comment,
    Complaint,
    Course,
    Enrollment,
    Lesson,
    Payment,
    Post,
    Question,
    Quiz,
    QuizSubmission,
    StudentProfile,
)


# 1. Allows adding Multiple Choices directly inside a Question page
class ChoiceInline(admin.TabularInline):
  model = Choice
  extra = 3  # Shows 3 blank choice rows by default


class QuestionAdmin(admin.ModelAdmin):
  inlines = [ChoiceInline]


# 2. Allows adding Multiple Lessons directly inside a Course setup page
class LessonInline(admin.StackedInline):
  model = Lesson
  extra = 1  # Gives you a clean layout to add lessons immediately
  show_change_link = True  # Quick link to manage deep settings like video urls


class CourseAdmin(admin.ModelAdmin):
  inlines = [LessonInline]
  list_display = ('title', 'instructor', 'course_pdf')


# 3. Custom display for Complaints management
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
  list_display = ('subject', 'user', 'status', 'created_at')
  list_filter = ('status', 'created_at')
  search_fields = ('subject', 'message', 'user__username')


# 4. Custom display for Student Profile & Fee Approval
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
  list_display = (
      'user',
      'matric_number',
      'payment_status',
      'has_paid_fees',
      'fee_receipt',
  )
  list_filter = ('payment_status', 'has_paid_fees', 'level', 'department')
  search_fields = (
      'user__username',
      'user__first_name',
      'user__last_name',
      'matric_number',
  )
  list_editable = (
      'payment_status',
  )  # Allows approving directly from the list view!


# 5. Custom display & bulk actions for Course Enrollments
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
  list_display = ('user', 'course', 'status', 'receipt', 'enrolled_at')
  list_filter = ('status', 'course')
  search_fields = ('user__username', 'course__title')
  list_editable = (
      'status',
  )  # Allows quick status changes directly in the table view
  actions = ['approve_enrollments', 'reject_enrollments']

  def approve_enrollments(self, request, queryset):
    updated = queryset.update(status='APPROVED')
    self.message_user(
        request, f'{updated} enrollment(s) approved and granted course access.'
    )

  approve_enrollments.short_description = 'Approve selected enrollments'

  def reject_enrollments(self, request, queryset):
    updated = queryset.update(status='REJECTED')
    self.message_user(request, f'{updated} enrollment(s) rejected.')

  reject_enrollments.short_description = 'Reject selected enrollments'


# Register remaining models
admin.site.register(Course, CourseAdmin)
admin.site.register(Quiz)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Lesson)
admin.site.register(QuizSubmission)
admin.site.register(Payment)
admin.site.register(Post)
admin.site.register(Comment)
