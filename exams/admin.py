from django.contrib import admin

from .models import Exam, Question, Choice, ExamAttempt, StudentAnswer


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'subject', 'is_published', 'start_time', 'end_time', 'question_count')
    list_filter = ('is_published', 'subject')
    search_fields = ('title', 'teacher__username')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'order', 'text', 'marks')
    list_filter = ('exam',)
    inlines = [ChoiceInline]


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'attempt_number', 'status', 'score', 'started_at', 'submitted_at')
    list_filter = ('status', 'exam')
    search_fields = ('student__username', 'exam__title')


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_choice', 'is_correct')
    list_filter = ('is_correct',)
