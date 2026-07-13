from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = 'api'

urlpatterns = [
    # ---- Auth ----
    path('auth/register/student/', views.StudentRegisterView.as_view(), name='register_student'),
    path('auth/register/teacher/', views.TeacherRegisterView.as_view(), name='register_teacher'),
    path('auth/verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('auth/resend-verification/', views.ResendVerificationView.as_view(), name='resend_verification'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ---- Profile ----
    path('profile/me/', views.MeView.as_view(), name='me'),

    # ---- Teacher: exams & questions ----
    path('teacher/exams/', views.TeacherExamListCreateView.as_view(), name='teacher_exam_list'),
    path('teacher/exams/<int:pk>/', views.TeacherExamDetailView.as_view(), name='teacher_exam_detail'),
    path('teacher/exams/<int:exam_id>/toggle-publish/', views.ExamTogglePublishView.as_view(), name='exam_toggle_publish'),
    path('teacher/exams/<int:exam_id>/questions/', views.QuestionListCreateView.as_view(), name='question_list_create'),
    path('teacher/exams/<int:exam_id>/questions/<int:question_id>/', views.QuestionDetailView.as_view(), name='question_detail'),
    path('teacher/exams/<int:exam_id>/results/', views.ExamResultsView.as_view(), name='exam_results'),
    path('teacher/attempts/<int:attempt_id>/review/', views.TeacherAttemptReviewView.as_view(), name='teacher_attempt_review'),

    # ---- Student: browsing & taking exams ----
    path('student/exams/available/', views.StudentAvailableExamsView.as_view(), name='student_exams_available'),
    path('student/exams/upcoming/', views.StudentUpcomingExamsView.as_view(), name='student_exams_upcoming'),
    path('student/exams/<int:exam_id>/start/', views.ExamStartView.as_view(), name='exam_start'),
    path('student/attempts/<int:attempt_id>/', views.AttemptStateView.as_view(), name='attempt_state'),
    path('student/attempts/<int:attempt_id>/answer/', views.SubmitAnswerView.as_view(), name='submit_answer'),
    path('student/attempts/<int:attempt_id>/submit/', views.SubmitExamView.as_view(), name='submit_exam'),
    path('student/attempts/<int:attempt_id>/review/', views.StudentAttemptReviewView.as_view(), name='student_attempt_review'),
    path('student/results/', views.MyResultsView.as_view(), name='my_results'),
]
