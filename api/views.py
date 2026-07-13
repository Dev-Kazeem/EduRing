from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import CustomUser
from accounts.utils import send_verification_email
from exams.models import Exam, Question, ExamAttempt, StudentAnswer

from .permissions import IsTeacher, IsStudent, IsExamOwner, IsAttemptOwner
from .serializers import (
    UserSerializer, ProfileUpdateSerializer,
    StudentSignUpSerializer, TeacherSignUpSerializer,
    EmailVerifySerializer, ResendVerificationSerializer,
    ExamSerializer, ExamDetailSerializer, QuestionSerializer,
    ExamAvailableSerializer, ExamAttemptStateSerializer,
    AnswerSubmitSerializer, ExamAttemptResultSerializer,
    AttemptReviewSerializer,
)


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


# =========================================================================
# AUTH
# =========================================================================

class StudentRegisterView(generics.CreateAPIView):
    serializer_class = StudentSignUpSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_verification_email(request, user)
        return Response(
            {'detail': 'Account created. Check your email to verify your address before logging in.'},
            status=status.HTTP_201_CREATED,
        )


class TeacherRegisterView(generics.CreateAPIView):
    serializer_class = TeacherSignUpSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_verification_email(request, user)
        return Response(
            {'detail': 'Account created. Check your email to verify your address before logging in.'},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])
        return Response({
            'detail': 'Email verified successfully.',
            'tokens': _tokens_for(user),
            'user': UserSerializer(user).data,
        })


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = CustomUser.objects.filter(
            email__iexact=serializer.validated_data['email'], is_active=False
        ).first()
        if user:
            send_verification_email(request, user)
        # Same response regardless, so this can't be used to enumerate accounts.
        return Response({'detail': 'If that email is registered and unverified, a new link is on its way.'})


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProfileUpdateSerializer
        return UserSerializer


# =========================================================================
# TEACHER: EXAMS
# =========================================================================

class TeacherExamListCreateView(generics.ListCreateAPIView):
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return Exam.objects.filter(teacher=self.request.user)

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class TeacherExamDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExamDetailSerializer
    permission_classes = [IsAuthenticated, IsTeacher, IsExamOwner]

    def get_queryset(self):
        return Exam.objects.filter(teacher=self.request.user)


class ExamTogglePublishView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id, teacher=request.user)
        if not exam.is_published and exam.question_count == 0:
            return Response(
                {'detail': 'Add at least one question before publishing.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        exam.is_published = not exam.is_published
        exam.save(update_fields=['is_published'])
        return Response(ExamSerializer(exam).data)


class QuestionListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_exam(self):
        return get_object_or_404(Exam, id=self.kwargs['exam_id'], teacher=self.request.user)

    def get_queryset(self):
        return self.get_exam().questions.all()

    def perform_create(self, serializer):
        serializer.save(exam=self.get_exam())


class QuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated, IsTeacher, IsExamOwner]
    lookup_url_kwarg = 'question_id'

    def get_queryset(self):
        return Question.objects.filter(exam__id=self.kwargs['exam_id'], exam__teacher=self.request.user)


class ExamResultsView(generics.ListAPIView):
    serializer_class = ExamAttemptResultSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        exam = get_object_or_404(Exam, id=self.kwargs['exam_id'], teacher=self.request.user)
        return exam.attempts.select_related('student', 'exam').exclude(status=ExamAttempt.Status.IN_PROGRESS)


class TeacherAttemptReviewView(generics.RetrieveAPIView):
    serializer_class = AttemptReviewSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_url_kwarg = 'attempt_id'

    def get_queryset(self):
        return ExamAttempt.objects.filter(exam__teacher=self.request.user).exclude(
            status=ExamAttempt.Status.IN_PROGRESS
        )


# =========================================================================
# STUDENT: BROWSE & TAKE EXAMS
# =========================================================================

class StudentAvailableExamsView(generics.ListAPIView):
    serializer_class = ExamAvailableSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        now = timezone.now()
        return Exam.objects.filter(
            is_published=True, start_time__lte=now, end_time__gte=now
        ).exclude(questions=None).distinct()


class StudentUpcomingExamsView(generics.ListAPIView):
    serializer_class = ExamAvailableSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        return Exam.objects.filter(is_published=True, start_time__gt=timezone.now())


class ExamStartView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id, is_published=True)

        if not exam.can_be_attempted_by(request.user):
            return Response(
                {'detail': "This exam isn't currently available to you (closed, not yet open, or no attempts left)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        in_progress = ExamAttempt.objects.filter(
            student=request.user, exam=exam, status=ExamAttempt.Status.IN_PROGRESS
        ).first()
        if in_progress:
            if in_progress.is_time_expired:
                in_progress.grade()
            else:
                return Response(
                    ExamAttemptStateSerializer(in_progress).data,
                    status=status.HTTP_200_OK,
                )

        attempt_number = exam.attempts_used_by(request.user) + 1
        attempt = ExamAttempt.objects.create(
            student=request.user, exam=exam, attempt_number=attempt_number
        )
        return Response(ExamAttemptStateSerializer(attempt).data, status=status.HTTP_201_CREATED)


class AttemptStateView(generics.RetrieveAPIView):
    """GET the current state of an attempt — in-progress questions/timer, or final result."""
    permission_classes = [IsAuthenticated, IsStudent, IsAttemptOwner]
    lookup_url_kwarg = 'attempt_id'

    def get_queryset(self):
        return ExamAttempt.objects.filter(student=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        attempt = self.get_object()
        if attempt.status == ExamAttempt.Status.IN_PROGRESS and attempt.is_time_expired:
            attempt.grade()

        if attempt.status == ExamAttempt.Status.IN_PROGRESS:
            return Response(ExamAttemptStateSerializer(attempt).data)
        return Response(ExamAttemptResultSerializer(attempt).data)


class SubmitAnswerView(APIView):
    """Autosave a single answer while the exam is in progress."""
    permission_classes = [IsAuthenticated, IsStudent, IsAttemptOwner]

    def post(self, request, attempt_id):
        attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=request.user)
        self.check_object_permissions(request, attempt)

        if attempt.status != ExamAttempt.Status.IN_PROGRESS:
            return Response({'detail': 'This attempt is already finished.'}, status=status.HTTP_400_BAD_REQUEST)
        if attempt.is_time_expired:
            attempt.grade()
            return Response({'detail': 'Time was up — the attempt has been auto-submitted.'},
                             status=status.HTTP_409_CONFLICT)

        serializer = AnswerSubmitSerializer(data=request.data, context={'attempt': attempt})
        serializer.is_valid(raise_exception=True)

        StudentAnswer.objects.update_or_create(
            attempt=attempt,
            question=serializer.validated_data['question'],
            defaults={'selected_choice': serializer.validated_data['choice']},
        )
        return Response({'detail': 'Answer saved.', 'seconds_remaining': attempt.seconds_remaining})


class SubmitExamView(APIView):
    """Finalize and grade an attempt. Optionally accepts a full batch of answers."""
    permission_classes = [IsAuthenticated, IsStudent, IsAttemptOwner]

    def post(self, request, attempt_id):
        attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=request.user)
        self.check_object_permissions(request, attempt)

        if attempt.status != ExamAttempt.Status.IN_PROGRESS:
            return Response(ExamAttemptResultSerializer(attempt).data)

        answers_payload = request.data.get('answers', [])
        if answers_payload:
            with transaction.atomic():
                for item in answers_payload:
                    serializer = AnswerSubmitSerializer(data=item, context={'attempt': attempt})
                    serializer.is_valid(raise_exception=True)
                    StudentAnswer.objects.update_or_create(
                        attempt=attempt,
                        question=serializer.validated_data['question'],
                        defaults={'selected_choice': serializer.validated_data['choice']},
                    )

        attempt.grade()
        return Response(ExamAttemptResultSerializer(attempt).data)


class StudentAttemptReviewView(generics.RetrieveAPIView):
    serializer_class = AttemptReviewSerializer
    permission_classes = [IsAuthenticated, IsStudent, IsAttemptOwner]
    lookup_url_kwarg = 'attempt_id'

    def get_queryset(self):
        return ExamAttempt.objects.filter(student=self.request.user).exclude(
            status=ExamAttempt.Status.IN_PROGRESS
        )


class MyResultsView(generics.ListAPIView):
    serializer_class = ExamAttemptResultSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        return ExamAttempt.objects.filter(student=self.request.user).exclude(
            status=ExamAttempt.Status.IN_PROGRESS
        ).select_related('exam')
