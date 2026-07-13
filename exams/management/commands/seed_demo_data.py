from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from exams.models import Exam, Question, Choice

User = get_user_model()


class Command(BaseCommand):
    help = "Creates a demo teacher, student, and a sample published exam so you can try the platform immediately."

    @transaction.atomic
    def handle(self, *args, **options):
        teacher, created = User.objects.get_or_create(
            username='teacher_demo',
            defaults=dict(
                email='teacher@example.com', first_name='Tina', last_name='Teacher',
                role=User.Role.TEACHER, department='Computer Science',
            ),
        )
        if created:
            teacher.set_password('demopass123')
            teacher.save()
            self.stdout.write(self.style.SUCCESS("Created teacher: teacher_demo / demopass123"))

        student, created = User.objects.get_or_create(
            username='student_demo',
            defaults=dict(
                email='student@example.com', first_name='Sam', last_name='Student',
                role=User.Role.STUDENT, roll_number='STU-001', grade_level='Year 1',
            ),
        )
        if created:
            student.set_password('demopass123')
            student.save()
            self.stdout.write(self.style.SUCCESS("Created student: student_demo / demopass123"))

        exam, created = Exam.objects.get_or_create(
            title='Python Basics Quiz',
            teacher=teacher,
            defaults=dict(
                description='A short quiz covering Python fundamentals.',
                subject='Computer Science',
                duration_minutes=15,
                start_time=timezone.now() - timedelta(minutes=5),
                end_time=timezone.now() + timedelta(days=7),
                pass_percentage=50,
                max_attempts=2,
                is_published=True,
            ),
        )
        if not created:
            self.stdout.write("Demo exam already exists — skipping question creation.")
            return

        questions_data = [
            {
                "text": "What keyword defines a function in Python?",
                "marks": 1,
                "order": 1,
                "choices": [("def", True), ("func", False), ("lambda", False), ("define", False)],
            },
            {
                "text": "Which data type is immutable in Python?",
                "marks": 1,
                "order": 2,
                "choices": [("list", False), ("dict", False), ("tuple", True), ("set", False)],
            },
            {
                "text": "What does len([1, 2, 3]) return?",
                "marks": 1,
                "order": 3,
                "choices": [("2", False), ("3", True), ("4", False), ("Error", False)],
            },
            {
                "text": "Which symbol is used for comments in Python?",
                "marks": 1,
                "order": 4,
                "choices": [("//", False), ("#", True), ("--", False), ("/*", False)],
            },
        ]

        for q_data in questions_data:
            question = Question.objects.create(
                exam=exam, text=q_data["text"], marks=q_data["marks"], order=q_data["order"]
            )
            for choice_text, is_correct in q_data["choices"]:
                Choice.objects.create(question=question, text=choice_text, is_correct=is_correct)

        self.stdout.write(self.style.SUCCESS(
            f"Created demo exam '{exam.title}' with {len(questions_data)} questions."
        ))
        self.stdout.write(self.style.SUCCESS("Demo data ready. Log in as student_demo or teacher_demo."))
