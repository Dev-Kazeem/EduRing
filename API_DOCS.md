# REST API Reference

Base path: `/api/`

Auth: JWT (via `djangorestframework-simplejwt`). Obtain a token pair, then send
`Authorization: Bearer <access_token>` on every subsequent request. Access
tokens live 1 hour; refresh tokens live 7 days and rotate on use.

All request/response bodies are JSON. Endpoints marked 🔓 are public; everything
else requires a valid access token, and 👨‍🏫/🎓 mark teacher-only / student-only
endpoints.

---

## Auth & account verification

### 🔓 `POST /api/auth/register/student/`
```json
{
  "username": "sam", "email": "sam@example.com",
  "first_name": "Sam", "last_name": "Student",
  "password": "correct-horse-1", "password2": "correct-horse-1",
  "roll_number": "STU-042", "grade_level": "Year 2"
}
```
Creates an **inactive** student account and emails a verification link.
`201` → `{"detail": "Account created. Check your email..."}`

### 🔓 `POST /api/auth/register/teacher/`
Same shape, with `department` instead of `roll_number`/`grade_level`.

### 🔓 `POST /api/auth/verify-email/`
```json
{"uidb64": "...", "token": "..."}
```
(Both values come from the link emailed to the user.) Activates the account and
immediately returns a usable token pair:
```json
{"detail": "Email verified successfully.", "tokens": {"access": "...", "refresh": "..."}, "user": {...}}
```

### 🔓 `POST /api/auth/resend-verification/`
```json
{"email": "sam@example.com"}
```
Always returns the same generic message, whether or not that email is registered
(prevents account enumeration).

### 🔓 `POST /api/auth/token/`
```json
{"username": "sam", "password": "correct-horse-1"}
```
→ `{"access": "...", "refresh": "..."}`. Fails for unverified (inactive) accounts.

### 🔓 `POST /api/auth/token/refresh/`
```json
{"refresh": "..."}
```
→ `{"access": "..."}` (and a new `refresh`, since rotation is on).

---

## Profile

### `GET /api/profile/me/`
Returns the logged-in user's full profile.

### `PUT` / `PATCH /api/profile/me/`
Update `first_name`, `last_name`, `email`, `phone_number`, `bio`,
`profile_picture`, plus `department` (teacher) or `roll_number`/`grade_level`
(student).

---

## 👨‍🏫 Teacher: exams

### `GET /api/teacher/exams/`
List exams you created (paginated). Each item includes `question_count` and
`total_marks`.

### `POST /api/teacher/exams/`
```json
{
  "title": "Python Basics", "description": "...", "subject": "CS",
  "duration_minutes": 15, "start_time": "2026-07-05T09:00:00Z",
  "end_time": "2026-07-12T09:00:00Z", "pass_percentage": "50.00",
  "max_attempts": 2, "shuffle_questions": true, "is_published": false
}
```

### `GET /api/teacher/exams/<id>/`
Full detail, including nested `questions` (with `is_correct` visible — this is
the owner's management view).

### `PUT` / `PATCH` / `DELETE /api/teacher/exams/<id>/`
Update or delete. 403 if you don't own it.

### `POST /api/teacher/exams/<id>/toggle-publish/`
Flips `is_published`. 400 if you try to publish with zero questions.

### `GET /api/teacher/exams/<id>/questions/`
List questions for the exam (with choices + `is_correct`).

### `POST /api/teacher/exams/<id>/questions/`
```json
{
  "text": "What keyword defines a function?", "marks": 1, "order": 1,
  "explanation": "def declares a function.",
  "choices": [
    {"text": "def", "is_correct": true},
    {"text": "func", "is_correct": false},
    {"text": "lambda", "is_correct": false}
  ]
}
```
Requires ≥2 choices and exactly one `is_correct: true`, or you get a `400` with
a field-level error.

### `GET` / `PUT` / `PATCH` / `DELETE /api/teacher/exams/<id>/questions/<question_id>/`
Manage a single question (PUT/PATCH replaces the whole `choices` list).

### `GET /api/teacher/exams/<id>/results/`
List every completed/timed-out attempt on this exam — student name, score,
percentage, pass/fail.

### `GET /api/teacher/attempts/<attempt_id>/review/`
One student's full answer breakdown for a specific attempt.

---

## 🎓 Student: browsing & taking exams

### `GET /api/student/exams/available/`
Exams that are published, currently within their open window, and have ≥1
question. Each item includes `attempts_used` and `can_attempt` for the calling
student.

### `GET /api/student/exams/upcoming/`
Published exams whose `start_time` hasn't arrived yet.

### `POST /api/student/exams/<exam_id>/start/`
Starts a new attempt (or resumes an existing in-progress one; auto-grades and
returns the result if that in-progress attempt already timed out). Returns the
exam-taking state:
```json
{
  "id": 7, "exam": 3, "exam_title": "Python Basics", "attempt_number": 1,
  "status": "IN_PROGRESS", "started_at": "...", "seconds_remaining": 900,
  "questions": [
    {"id": 1, "text": "...", "marks": 1, "order": 1,
     "choices": [{"id": 1, "text": "def"}, {"id": 2, "text": "func"}]}
  ],
  "existing_answers": {}
}
```
Note `choices` here never include `is_correct`.

### `GET /api/student/attempts/<attempt_id>/`
Poll this while taking the exam. Returns the same shape as `start/` while
`IN_PROGRESS` (auto-grading first if time has actually run out), or the final
result shape (see below) once finished.

### `POST /api/student/attempts/<attempt_id>/answer/`
Autosave one answer as the student picks it:
```json
{"question_id": 1, "choice_id": 2}
```
Send `"choice_id": null` to clear an answer. `409` if the timer had already run
out (the attempt is auto-submitted for you in that case).

### `POST /api/student/attempts/<attempt_id>/submit/`
Finalizes and grades the attempt. You can optionally send a full batch of
answers in one call instead of (or in addition to) calling `/answer/`
repeatedly:
```json
{"answers": [{"question_id": 1, "choice_id": 2}, {"question_id": 2, "choice_id": 5}]}
```
Returns the result:
```json
{
  "id": 7, "exam": 3, "exam_title": "Python Basics", "student": "sam",
  "attempt_number": 1, "status": "COMPLETED", "score": "3.00",
  "total_marks": 4, "percentage": "75.00", "passed": true,
  "started_at": "...", "submitted_at": "..."
}
```

### `GET /api/student/attempts/<attempt_id>/review/`
Full answer breakdown after completion — every choice, which one you picked,
which one was correct, and any teacher explanation. `400` if the attempt is
still in progress.

### `GET /api/student/results/`
List of all your completed/timed-out attempts across every exam.

---

## Error format

Validation errors follow DRF's default shape:
```json
{"password2": ["Passwords don't match."]}
```
Permission failures return `403` with `{"detail": "..."}`; not-found/not-yours
returns `404`.

## Rate limits

Anonymous requests: 20/min. Authenticated requests: 120/min (tune via
`REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` in `settings.py`).
