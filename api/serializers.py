from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from accounts.tokens import account_activation_token
from exams.models import Exam, Question, Choice, ExamAttempt, StudentAnswer

User = get_user_model()


# =========================================================================
# ACCOUNTS
# =========================================================================

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'role',
            'phone_number', 'bio', 'profile_picture', 'department',
            'roll_number', 'grade_level', 'date_joined',
        ]
        read_only_fields = ['id', 'role', 'date_joined']


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'bio',
            'profile_picture', 'department', 'roll_number', 'grade_level',
        ]


class BaseSignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8, label="Confirm password")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': "Passwords don't match."})
        validate_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data, is_active=False, role=self.role)
        user.set_password(password)
        user.save()
        return user


class StudentSignUpSerializer(BaseSignUpSerializer):
    role = User.Role.STUDENT
    roll_number = serializers.CharField(required=False, allow_blank=True)
    grade_level = serializers.CharField(required=False, allow_blank=True)

    class Meta(BaseSignUpSerializer.Meta):
        fields = BaseSignUpSerializer.Meta.fields + ['roll_number', 'grade_level']


class TeacherSignUpSerializer(BaseSignUpSerializer):
    role = User.Role.TEACHER
    department = serializers.CharField(required=False, allow_blank=True)

    class Meta(BaseSignUpSerializer.Meta):
        fields = BaseSignUpSerializer.Meta.fields + ['department']


class EmailVerifySerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uidb64']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("This verification link is invalid.")

        if not account_activation_token.check_token(user, attrs['token']):
            raise serializers.ValidationError("This verification link is invalid or has expired.")

        attrs['user'] = user
        return attrs


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


# =========================================================================
# EXAMS — teacher-facing
# =========================================================================

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'marks', 'order', 'explanation', 'choices']

    def validate_choices(self, choices):
        filled = [c for c in choices if c.get('text')]
        if len(filled) < 2:
            raise serializers.ValidationError("Provide at least 2 answer choices.")
        correct_count = sum(1 for c in filled if c.get('is_correct'))
        if correct_count != 1:
            raise serializers.ValidationError("Mark exactly one choice as correct.")
        return choices

    def create(self, validated_data):
        choices_data = validated_data.pop('choices')
        question = Question.objects.create(**validated_data)
        for choice_data in choices_data:
            Choice.objects.create(question=question, **choice_data)
        return question

    def update(self, instance, validated_data):
        choices_data = validated_data.pop('choices', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if choices_data is not None:
            instance.choices.all().delete()
            for choice_data in choices_data:
                Choice.objects.create(question=instance, **choice_data)
        return instance


class ExamSerializer(serializers.ModelSerializer):
    question_count = serializers.ReadOnlyField()
    total_marks = serializers.ReadOnlyField()
    teacher = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Exam
        fields = [
            'id', 'teacher', 'title', 'description', 'subject', 'duration_minutes',
            'start_time', 'end_time', 'pass_percentage', 'max_attempts',
            'shuffle_questions', 'is_published', 'question_count', 'total_marks',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'teacher', 'created_at', 'updated_at']

    def validate(self, attrs):
        start = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end = attrs.get('end_time', getattr(self.instance, 'end_time', None))
        if start and end and end <= start:
            raise serializers.ValidationError("End time must be after start time.")
        return attrs


class ExamDetailSerializer(ExamSerializer):
    """Exam detail for the owning teacher, including full question bank with answers."""
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(ExamSerializer.Meta):
        fields = ExamSerializer.Meta.fields + ['questions']


# =========================================================================
# EXAMS — student-facing
# =========================================================================

class ChoiceStudentSerializer(serializers.ModelSerializer):
    """Choices as seen by a student taking the exam — no `is_correct` leak."""
    class Meta:
        model = Choice
        fields = ['id', 'text']


class QuestionStudentSerializer(serializers.ModelSerializer):
    choices = ChoiceStudentSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'marks', 'order', 'choices']


class ExamAvailableSerializer(serializers.ModelSerializer):
    question_count = serializers.ReadOnlyField()
    total_marks = serializers.ReadOnlyField()
    attempts_used = serializers.SerializerMethodField()
    can_attempt = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            'id', 'title', 'description', 'subject', 'duration_minutes',
            'start_time', 'end_time', 'pass_percentage', 'max_attempts',
            'question_count', 'total_marks', 'attempts_used', 'can_attempt',
        ]

    def get_attempts_used(self, exam):
        return exam.attempts_used_by(self.context['request'].user)

    def get_can_attempt(self, exam):
        return exam.can_be_attempted_by(self.context['request'].user)


class AnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    choice_id = serializers.IntegerField(allow_null=True, required=False)

    def validate(self, attrs):
        attempt = self.context['attempt']
        try:
            question = attempt.exam.questions.get(id=attrs['question_id'])
        except Question.DoesNotExist:
            raise serializers.ValidationError({'question_id': "That question isn't part of this exam."})

        choice = None
        choice_id = attrs.get('choice_id')
        if choice_id is not None:
            choice = question.choices.filter(id=choice_id).first()
            if choice is None:
                raise serializers.ValidationError({'choice_id': "That choice doesn't belong to this question."})

        attrs['question'] = question
        attrs['choice'] = choice
        return attrs


class ExamAttemptStateSerializer(serializers.ModelSerializer):
    """Full state needed by a client to render the in-progress exam-taking screen."""
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    seconds_remaining = serializers.ReadOnlyField()
    questions = serializers.SerializerMethodField()
    existing_answers = serializers.SerializerMethodField()

    class Meta:
        model = ExamAttempt
        fields = [
            'id', 'exam', 'exam_title', 'attempt_number', 'status',
            'started_at', 'seconds_remaining', 'questions', 'existing_answers',
        ]

    def get_questions(self, attempt):
        questions = attempt.exam.questions.prefetch_related('choices').order_by('order', 'id')
        return QuestionStudentSerializer(questions, many=True).data

    def get_existing_answers(self, attempt):
        return {
            answer.question_id: answer.selected_choice_id
            for answer in attempt.answers.all()
        }


class ExamAttemptResultSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    total_marks = serializers.IntegerField(source='exam.total_marks', read_only=True)
    percentage = serializers.ReadOnlyField()
    passed = serializers.ReadOnlyField()
    student = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ExamAttempt
        fields = [
            'id', 'exam', 'exam_title', 'student', 'attempt_number', 'status', 'score',
            'total_marks', 'percentage', 'passed', 'started_at', 'submitted_at',
        ]


class StudentAnswerReviewSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    marks = serializers.IntegerField(source='question.marks', read_only=True)
    explanation = serializers.CharField(source='question.explanation', read_only=True)
    choices = serializers.SerializerMethodField()
    selected_choice_id = serializers.IntegerField(source='selected_choice.id', read_only=True)

    class Meta:
        model = StudentAnswer
        fields = [
            'question', 'question_text', 'marks', 'explanation',
            'choices', 'selected_choice_id', 'is_correct',
        ]

    def get_choices(self, answer):
        return [
            {'id': c.id, 'text': c.text, 'is_correct': c.is_correct}
            for c in answer.question.choices.all()
        ]


class AttemptReviewSerializer(ExamAttemptResultSerializer):
    answers = StudentAnswerReviewSerializer(many=True, read_only=True)

    class Meta(ExamAttemptResultSerializer.Meta):
        fields = ExamAttemptResultSerializer.Meta.fields + ['answers']
