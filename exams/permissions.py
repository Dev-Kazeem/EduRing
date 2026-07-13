from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def teacher_required(view_func):
    """Function-based view decorator: only Teachers may proceed."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_teacher:
            messages.error(request, "That page is only available to teachers.")
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


def student_required(view_func):
    """Function-based view decorator: only Students may proceed."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_student:
            messages.error(request, "That page is only available to students.")
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Class-based view mixin: only Teachers may access."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_teacher

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('accounts:login')
        messages.error(self.request, "That page is only available to teachers.")
        return redirect('accounts:dashboard')


class StudentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Class-based view mixin: only Students may access."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_student

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('accounts:login')
        messages.error(self.request, "That page is only available to students.")
        return redirect('accounts:dashboard')
