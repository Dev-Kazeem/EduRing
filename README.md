# Online Multiple-Choice Exam Platform

A Django web application for running online multiple-choice exams, with two
distinct user roles: **Teacher** and **Student**.

## Features

### Accounts
- Custom user model (`accounts.CustomUser`) with a `role` field (`STUDENT` / `TEACHER`)
- Separate sign-up flows for students and teachers, each capturing role-relevant details
  (roll number/grade for students, department for teachers)
- Login, logout, password change
- Editable profile with photo, bio, and contact info
- Role-based dashboard redirect after login

### Teacher capabilities
- Create, edit, delete exams (title, description, subject, duration, availability window,
  pass percentage, max attempts, question shuffling, publish/draft state)
- Add/edit/delete multiple-choice questions, each with 2–6 answer choices and exactly
  one correct answer (validated by a formset)
- Publish/unpublish exams (an exam can't be published with zero questions)
- View a results table for every student attempt on an exam, with score, percentage, and pass/fail
- Drill into any individual student's attempt to see exactly which answers were right/wrong
- Ownership enforcement — teachers can only manage their own exams

### Student capabilities
- Dashboard of currently available exams (published + within the open time window),
  with attempts-remaining tracking
- Upcoming (not-yet-open) exams listed separately
- Take an exam with a live countdown timer that **auto-submits** when time runs out
- Resume an in-progress attempt if the page is reloaded (answers are saved on submit)
- Automatic grading immediately after submission
- Full answer review after submission: correct answer, what you picked, and any
  teacher-provided explanation
- History of all past results with score/percentage/pass-fail

### Platform-wide
- Enforced per-role access control (a student can't reach teacher views and vice versa)
- Attempt limits (`max_attempts` per exam) and exam time windows enforced server-side,
  not just in the UI
- Auto-grading logic lives on the model (`ExamAttempt.grade()`), so it's consistent
  whether triggered by submission or by time-expiry
- Django admin fully wired up for both apps (manage users, exams, questions, attempts)
- Bootstrap 5 UI, mobile-responsive

## Project layout

```
online_exam_platform/
├── manage.py
├── requirements.txt
├── exam_platform/       # project settings, root urls
├── accounts/            # CustomUser, registration, profile
├── exams/                # Exam, Question, Choice, ExamAttempt, StudentAnswer
├── templates/            # all HTML templates (Bootstrap 5)
└── static/                # css/js
```

## Setup

1. **Create a virtual environment and install dependencies**

   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create an admin superuser** (optional, for `/admin/`)

   ```bash
   python manage.py createsuperuser
   ```

4. **(Optional) Seed demo data** — creates a demo teacher, demo student, and a
   published sample exam so you can try the whole flow immediately:

   ```bash
   python manage.py seed_demo_data
   ```

   This creates:
   - Teacher login: `teacher_demo` / `demopass123`
   - Student login: `student_demo` / `demopass123`

5. **Run the development server**

   ```bash
   python manage.py runserver
   ```

   Visit `http://127.0.0.1:8000/`.

## Typical workflow

**As a teacher:**
1. Sign up / log in as a teacher.
2. "Create Exam" → fill in title, timing window, duration, pass percentage.
3. You're redirected to "Manage Questions" → "Add Question" → enter the question
   text and choices, marking one as correct.
4. Once you have at least one question, go back to "My Exams" and click the
   eye icon to publish it.
5. As students complete it, view "Results" for a scoreboard, and click "Review"
   on any row to see exactly what that student answered.

**As a student:**
1. Sign up / log in as a student.
2. "Available Exams" shows anything published and currently open.
3. Click "Start Exam" — the timer begins immediately and the page will
   auto-submit when it hits zero.
4. After submitting, you're shown your score and a full answer breakdown.
5. "My Results" keeps a history of every attempt.

## Notes for production deployment

- Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, and `DJANGO_ALLOWED_HOSTS`
  as environment variables rather than relying on the defaults in `settings.py`.
- Swap the SQLite database for PostgreSQL (or similar) by updating `DATABASES`.
- Serve static/media files via a proper web server or storage backend
  (e.g. WhiteNoise, S3) instead of Django's development server.
- Put the app behind HTTPS and enable the commented-out `SECURE_*` settings.
